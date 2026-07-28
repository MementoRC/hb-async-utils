"""Tests for async_utils.hb_compat.common — the hb-logger integration shim."""

import logging

from logger import HummingbotLogger

from async_utils.hb_compat import get_logger


def test_get_logger_returns_hummingbot_logger():
    result = get_logger("async_utils.test_hb_compat")
    assert isinstance(result, HummingbotLogger)


def test_get_logger_returns_same_instance_as_stdlib_getlogger():
    name = "async_utils.test_hb_compat.same_instance"
    assert get_logger(name) is logging.getLogger(name)
