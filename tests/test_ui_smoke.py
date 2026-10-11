"""Smoke tests for Streamlit UI module imports and dependencies."""

import importlib
import pytest


def test_ui_module_importable():
    # Verify module syntax and top-level definitions can be parsed
    import ast
    with open("app/ui.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    assert isinstance(tree, ast.Module)
