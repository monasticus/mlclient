from __future__ import annotations

import logging

import pytest

from mlclient.logging import setup_logger


@pytest.fixture
def mlclient_logger() -> logging.Logger:
    """Configure the mlclient logger as ``ml`` does and restore it afterwards."""
    logger = logging.getLogger("mlclient")
    handlers, level, propagate = logger.handlers, logger.level, logger.propagate
    setup_logger()
    yield logger
    logger.handlers, logger.propagate = handlers, propagate
    logger.setLevel(level)
