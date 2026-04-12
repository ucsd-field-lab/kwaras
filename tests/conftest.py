"""Pytest fixtures for Kwaras tests."""

import json
import tempfile
from pathlib import Path
from typing import Dict

import pytest


@pytest.fixture
def valid_lexicon_config() -> Dict[str, str]:
    """Valid lexicon configuration."""
    return {"EAFL_DIR": "lexicons/Mixtec", "LIFT": "lexicons/Mixtec/Mixtec.lift"}


@pytest.fixture
def valid_corpus_config() -> Dict[str, str]:
    """Valid corpus configuration."""
    return {
        "LANGUAGE": "Mixtec",
        "FILE_DIR": "audio/Mixtec",
        "OLD_EAFS": "eaf/Mixtec",
        "WWW": "web/Mixtec",
    }


@pytest.fixture
def temp_config_file(valid_lexicon_config):
    """Create a temporary config file with valid lexicon config."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cfg", delete=False, encoding="utf-8"
    ) as f:
        json.dump(valid_lexicon_config, f)
        return Path(f.name)


@pytest.fixture
def temp_corpus_config_file(valid_corpus_config):
    """Create a temporary config file with valid corpus config."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cfg", delete=False, encoding="utf-8"
    ) as f:
        json.dump(valid_corpus_config, f)
        return Path(f.name)


@pytest.fixture
def temp_invalid_json_config():
    """Create a temporary config file with invalid JSON."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cfg", delete=False, encoding="utf-8"
    ) as f:
        f.write("{ invalid json }")
        return Path(f.name)


@pytest.fixture
def temp_empty_config():
    """Create a temporary empty config file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cfg", delete=False, encoding="utf-8"
    ) as f:
        f.write("")
        return Path(f.name)
