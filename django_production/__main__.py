import os
import sys
from importlib import import_module
from pathlib import Path
from string import Template
from types import ModuleType

import django

START_MARKER = "\n# BEGIN: added by django-production"
END_MARKER = "# END: added by django-production\n"


def patch_settings(settings: ModuleType) -> None:
    settings_file = Path(settings.__file__)
    production_settings_file = Path(__file__).parent / "settings.py"
    if START_MARKER in settings_file.read_text():
        raise RuntimeError(
            "It looks like this settings file already contains the django-production patch."
        )
    # assuming top-level module is the project
    # used to determine where static files directories should live
    settings_module_depth = len(settings.__name__.split(".")) - 2
    if settings_module_depth < 0:
        settings_module_depth = 0
    settings_patch = Template(production_settings_file.read_text()).safe_substitute(
        settings_depth=str(settings_module_depth)
    )
    with settings_file.open(mode="a") as f:
        f.write("\n".join([START_MARKER, settings_patch, END_MARKER]))


def patch_urlconf(settings: ModuleType) -> None:
    urlconf = settings.ROOT_URLCONF
    urlconf_mod = import_module(urlconf)
    urlconf_file = Path(urlconf_mod.__file__)
    if START_MARKER in urlconf_file.read_text():
        raise RuntimeError(
            "It looks like this urlconf file already contains the django-production patch."
        )
    patch_parts = [
        START_MARKER,
        "from django.urls import include",
        'urlpatterns.insert(0, path("-/", include("django_alive.urls")))',
        END_MARKER,
    ]
    with urlconf_file.open(mode="a") as f:
        f.write("\n".join(patch_parts))


def do_patch():
    # if Django project isn't installed, add the current directory to the Python path so it can be imported
    sys.path.insert(0, os.getcwd())
    django.setup()
    settings = import_module(os.environ["DJANGO_SETTINGS_MODULE"])
    patch_settings(settings)
    patch_urlconf(settings)
