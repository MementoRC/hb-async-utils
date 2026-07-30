"""hb_compat — isolates the ``hb-logger`` dependency for async_utils.

Internal call sites import ``get_logger`` from here instead of calling
``logging.getLogger`` directly against the stdlib. See ADR 0001 Group D.
"""

from async_utils.hb_compat.common import get_logger

__all__ = ["get_logger"]
