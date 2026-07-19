import importlib


def test_app_main_imports():
    module = importlib.import_module("app.main")

    assert module.app.title == "Mubify"
