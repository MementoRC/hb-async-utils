"""Canonical logger factory wrapping ``hb-logger`` for async_utils.

Isolates the external ``hb-logger`` import here so the rest of this
package never touches ``logging.getLogger`` (or ``hb-logger`` itself)
directly. Importing ``logger`` registers ``HummingbotLogger`` as the
active ``logging.Logger`` subclass via ``logging.setLoggerClass``, so
any logger returned by :func:`get_logger` afterwards is a
``HummingbotLogger`` instance with the ``notify``/``network``
extensions. See ADR 0001 Group D.
"""

import logging

# Importing `logger` registers HummingbotLogger as the active logging class.
import logger as _hb_logger  # type: ignore[import-untyped]  # noqa: F401

__all__ = ["get_logger"]


def get_logger(name: str) -> logging.Logger:
    """Return an hb-logger-backed logger for ``name``."""
    return logging.getLogger(name)
