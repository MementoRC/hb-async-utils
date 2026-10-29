"""hb_compat — thin stdlib logging helper kept for public API compatibility.

async_utils itself uses ``logging.getLogger(__name__)``; ``get_logger`` remains
exported for existing consumers. See ADR 0001 (L0 independence).
"""

from async_utils.hb_compat.common import get_logger

__all__ = ["get_logger"]
