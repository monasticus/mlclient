"""Opt-in logging configuration for MLClient applications."""

import logging.config

import yaml

from mlclient import _utils as utils


def setup_logger():
    """Set up MLClient logging configuration."""
    with utils.get_resource("logging.yaml") as config_file:
        config = yaml.safe_load(config_file.read())
        logging.config.dictConfig(config)


__all__ = ["setup_logger"]
