"""Shared pytest fixtures for hb-async-utils tests."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
