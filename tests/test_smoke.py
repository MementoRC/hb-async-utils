"""Smoke tests — verifies the package is importable and version is set."""

import pytest

import async_utils


@pytest.mark.unit
def test_import() -> None:
    """Package imports without error."""
    assert async_utils is not None


@pytest.mark.unit
def test_version_is_set() -> None:
    """__version__ is a non-empty string."""
    assert isinstance(async_utils.__version__, str)
    assert async_utils.__version__ != ""
