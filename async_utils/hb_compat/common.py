"""Thin stdlib logger factory for async_utils.

async_utils is an L0 package and must not depend on ``hb-logger`` (ADR 0001).
Handlers and the ``HummingbotLogger`` class are configured by hb-logger at the
application level; this module only exposes ``logging.getLogger``.
"""

import logging

__all__ = ["get_logger"]


def get_logger(name: str) -> logging.Logger:
    """Return the stdlib logger for ``name``."""
    return logging.getLogger(name)
