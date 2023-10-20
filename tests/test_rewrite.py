import ast
import io
from pathlib import Path

import pytest
from django_upgrade.data import Settings
from tokenize_rt import tokens_to_src

from django_production.main import apply_fixers

# # Define a fixture to create an in-memory file with content
# @pytest.fixture
# def temporary_settings_file(tmp_path) -> [str, str]:
#     content = (Path(__file__).parent / "default_django_settings.py").read_text()
#     tmp_settings = tmp_path / "settings.py"
#     tmp_settings.write_text(content)
#     return content, str(tmp_settings.name)
#
# def test_visit(temporary_settings_file):
#     contents, filename = temporary_settings_file
#     src = apply_fixers(contents, Settings(target_version=(5,0)), filename)
#     assert '    "django_webserver",' in src.splitlines()
