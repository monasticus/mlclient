"""Send an application's log records to both the console and MarkLogic."""

import logging

from mlclient.logging import MLLogHandler


def build_logger() -> logging.Logger:
    """Return a logger that writes to the console and a MarkLogic error log.

    The console handler keeps the usual timestamp and level. The MarkLogic
    handler omits both, because the server prepends its own timestamp and renders
    the level from the ``xdmp:log`` call.
    """
    logger = logging.getLogger("my_app")
    logger.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"),
    )
    logger.addHandler(console)

    marklogic = MLLogHandler(host="localhost", port=8000, auth="basic")
    marklogic.setFormatter(logging.Formatter("%(name)s - %(message)s"))
    logger.addHandler(marklogic)

    return logger
