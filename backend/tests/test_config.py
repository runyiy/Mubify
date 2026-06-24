import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pydantic_settings
import pytest


CONFIG_PATH = Path(__file__).resolve().parents[1] / "app" / "core" / "config.py"


def load_config_without_dotenv(monkeypatch, module_name, environment):
    original_settings_config_dict = pydantic_settings.SettingsConfigDict

    def settings_config_without_dotenv(**kwargs):
        kwargs["env_file"] = None
        return original_settings_config_dict(**kwargs)

    monkeypatch.setattr(
        pydantic_settings,
        "SettingsConfigDict",
        settings_config_without_dotenv,
    )

    spec = importlib.util.spec_from_file_location(module_name, CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        with patch.dict(os.environ, environment, clear=True):
            spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)

    return module


def test_missing_database_url_has_clear_error(monkeypatch):
    with pytest.raises(RuntimeError) as exc_info:
        load_config_without_dotenv(
            monkeypatch,
            "test_config_missing_database_url",
            {"SECRET_KEY": "test-secret-key"},
        )

    message = str(exc_info.value)

    assert "Missing backend configuration" in message
    assert "DATABASE_URL" in message
    assert "backend/.env.example" in message


def test_missing_secret_key_has_clear_error(monkeypatch):
    with pytest.raises(RuntimeError) as exc_info:
        load_config_without_dotenv(
            monkeypatch,
            "test_config_missing_secret_key",
            {"DATABASE_URL": "sqlite://"},
        )

    message = str(exc_info.value)

    assert "Missing backend configuration" in message
    assert "SECRET_KEY" in message
    assert "backend/.env.example" in message
