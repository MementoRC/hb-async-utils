"""
Tools for running asynchronous functions multiple times.
"""

import asyncio
import functools
import logging
from typing import Any

_LOGGER = logging.getLogger("retry")


class AllTriesFailedError(EnvironmentError):
    """Raised when all retry attempts have failed."""

    pass


# Backward-compatibility alias — will be removed in a future release
AllTriesFailedException = AllTriesFailedError  # noqa: N818


def async_retry(
    retry_count: int = 2,
    exception_types: list[type[Exception]] | None = None,
    logger: logging.Logger | None = None,
    stats: dict[str, int] | None = None,
    raise_exp: bool = True,
    retry_interval: float = 0.5,
):
    """
    A decorator for async functions that will retry a function x times, where x is retry_count.

    :param retry_count: Number of retries
    :param exception_types: All exceptions trigger retry, but exceptions in the list also get logging
    :param logger: if raise_exp is false then log the last exception instead of raising it
    :param stats:
    :param raise_exp: raise an exception if all retries failed, otherwise log the last exception
    :param retry_interval: time to wait between retries
    """
    if exception_types is None:
        exception_types = [Exception]
    if logger is None:
        logger = _LOGGER

    def decorator(fn):
        @functools.wraps(fn)
        async def retry(*args, _stats=stats, **kwargs):
            last_exception: Exception | None = None
            for count in range(1, retry_count + 1):
                try:
                    additional_params: dict[str, Any] = {}
                    fn_kwargs = {**additional_params, **kwargs}
                    return await fn(*args, **fn_kwargs)

                except tuple(exception_types) as exc:
                    last_exception = exc
                    logger.info(
                        f"Exception raised for {last_exception}: {fn.__name__}."
                        f" Retrying {count}/{retry_count} times."
                    )
                    if _stats is not None and type(_stats) is dict:
                        metric_name: str = f"retry.{fn.__name__}.count"
                        if metric_name not in _stats:
                            _stats[metric_name] = 1
                        else:
                            _stats[metric_name] += 1
                except Exception as exc:
                    last_exception = exc
                    raise
                await asyncio.sleep(retry_interval)
            if raise_exp:
                raise AllTriesFailedError() from last_exception
            else:
                logger.info(
                    f"Last exception raised for {repr(last_exception)}: {fn.__name__}. aborting."
                )

        return retry

    return decorator
