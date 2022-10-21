import os
import secrets
import shutil
import subprocess
from importlib import reload
from pathlib import Path

import pytest
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
    subprocess.check_call(["./manage.py", "check", "--deploy", "--fail-level=DEBUG"])
