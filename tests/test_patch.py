import os
import secrets
import shutil
import subprocess
import time
from contextlib import contextmanager
from importlib import reload
from pathlib import Path
from typing import Dict, List

import pytest
import urllib3
from django.core.exceptions import ImproperlyConfigured

from django_production.__main__ import START_MARKER, do_patch


@pytest.fixture(autouse=True)
def setup_testproj(tmpdir_factory):
    """Create an empty project and set DJANGO_SETTINGS_MODULE"""
    orig_env = os.environ.get("DJANGO_SETTINGS_MODULE")
    orig_dir = os.getcwd()
    os.environ["DJANGO_SETTINGS_MODULE"] = "testproj.settings"
    tmpdir = tmpdir_factory.mktemp("test")
    os.chdir(tmpdir)
    subprocess.check_call(["django-admin", "startproject", "testproj"])
    os.chdir("testproj")
    os.mkdir("testproj/static")
    yield
    os.chdir(orig_dir)
    shutil.rmtree(tmpdir)
    if orig_env is not None:
        os.environ["DJANGO_SETTINGS_MODULE"] = orig_env


@pytest.fixture
def django_env_prod():
    """Set expected production environment variables"""
    orig_env = os.environ.copy()
    os.environ.update(
        {
            "DJANGO_ENV": "production",
            "SECRET_KEY": secrets.token_urlsafe(60),
            "SECURE_HSTS_INCLUDE_SUBDOMAINS": "true",
        }
    )
    yield
    os.environ = orig_env


@contextmanager
def start_server(cmd: List[str], env: Dict[str, str]):
    """Start and terminate a server process in the background"""
    proc = subprocess.Popen(cmd, env=env)
    try:
        time.sleep(2)
        yield
    finally:
        proc.terminate()


def test_missing_env_var():
    """Patching fails without DJANGO_SETTINGS_MODULE"""
    del os.environ["DJANGO_SETTINGS_MODULE"]
    with pytest.raises(ImproperlyConfigured):
        do_patch()


def test_cli():
    """CLI is installed properly"""
    subprocess.check_call(["django-production-apply"])
    assert START_MARKER in Path("testproj/urls.py").read_text()
    assert START_MARKER in Path("testproj/settings.py").read_text()


def test_idempotent():
    """Patch is only applied once"""
    settings_file = Path("testproj/settings.py")
    orig_settings = settings_file.read_text()
    do_patch()
    with pytest.raises(RuntimeError):
        do_patch()
    settings_file.write_text(orig_settings)
    with pytest.raises(RuntimeError):
        do_patch()


def test_python():
    """Python code is functional after patching"""
    do_patch()
    from testproj import urls

    reload(urls)
    assert len(urls.urlpatterns) == 2

    from testproj import settings

    reload(settings)
    assert "django_webserver" in settings.INSTALLED_APPS


def test_django_env_dev():
    """Production settings are not applied in development"""
    do_patch()
    from testproj import settings

    reload(settings)
    assert settings.DEBUG is True
    assert not hasattr(settings, "CSRF_COOKIE_SECURE")


def test_django_env_prod(django_env_prod):
    """Production settings are applied in production"""
    do_patch()
    from testproj import settings

    reload(settings)
    assert settings.DEBUG is False
    assert settings.CSRF_COOKIE_SECURE is True


def test_django_check_deploy(django_env_prod):
    """django check --deploy passes after patching"""
    do_patch()
    # Use subprocess to make sure all the settings are loaded fresh post-patching
    subprocess.check_call(["./manage.py", "check", "--deploy", "--fail-level=DEBUG"])


def test_staticfiles_prod(django_env_prod):
    """Static files are served in production with cache headers"""
    Path("testproj/static/test.css").write_text("body { color: red; }")
    do_patch()
    subprocess.check_call(["./manage.py", "collectstatic", "--noinput"])
    with start_server(
        cmd=["./manage.py", "gunicorn"], env={"WEB_CONCURRENCY": "1", **os.environ}
    ):
        http = urllib3.PoolManager()
        resp = http.request(
            "GET",
            "http://localhost:8000/static/test.f2b804d3e3bd.css",
            headers={"X-Forwarded-Proto": "https"},
            redirect=False,
        )
    assert resp.status == 200
    assert resp.headers["Cache-Control"] == "max-age=315360000, public, immutable"


def test_staticfiles_dev():
    """Static files are served in development"""
    Path("testproj/static/test.css").write_text("body { color: red; }")
    do_patch()
    with start_server(cmd=["./manage.py", "runserver"], env=dict(os.environ)):
        http = urllib3.PoolManager()
        resp = http.request(
            "GET", "http://localhost:8000/static/test.css", redirect=False
        )
    assert resp.status == 200
    assert "Cache-Control" not in resp.headers
