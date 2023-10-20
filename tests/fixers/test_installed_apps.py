from __future__ import annotations

from django_upgrade.data import Settings

from tests.fixers.tools import check_noop, check_transformed

settings = Settings(target_version=(999, 0))


def test_noop():
    check_noop(
        """\
        INSTALLED_APPS = ["django_webserver", "whitenoise.runserver_nostatic"]
        """,
        settings,
        filename="settings.py",
    )


def test_updated():
    check_transformed(
        """\
        INSTALLED_APPS = ["appone", "apptwo"]
        """,
        """\
        INSTALLED_APPS = [
            "appone",
            "apptwo",
            "django_webserver",
            "whitenoise.runserver_nostatic",
        ]
        """,
        settings,
        filename="settings.py",
    )
