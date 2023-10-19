import io
from pathlib import Path

import pytest
from django_production.modifiers import add_imports

# Define a fixture to create an in-memory file with content
@pytest.fixture
def temporary_settings_file(tmp_path) -> [str, str]:
    content = (Path(__file__).parent / "default_django_settings.py").read_text()
    tmp_settings = tmp_path / "settings.py"
    tmp_settings.write_text(content)
    return content, str(tmp_settings.name)


def test_imports_added(temporary_settings_file):
    contents, filename = temporary_settings_file
    modded = add_imports(contents, filename)

    # Check if 'os' import has been added
    assert "import os" in modded.splitlines()
