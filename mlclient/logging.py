"""Opt-in logging configuration and MarkLogic log forwarding for applications.

``setup_logger`` configures MLClient's own diagnostic logging. ``MLLogHandler``
and ``setup_ml_logger`` let an application send its ordinary log records to a
MarkLogic server's error log alongside its usual handlers.

Which loggers reach the server is ordinary logging configuration: attach the
handler to the loggers whose records should be forwarded (the root logger to
forward everything, including third-party libraries, or named loggers to narrow
it). The handler only suppresses the records its own MarkLogic client emits while
forwarding, so attaching it to the root logger does not cause a feedback loop.
"""

from __future__ import annotations

import logging.config
import queue
import threading
from copy import deepcopy
from pathlib import Path

import yaml

from mlclient import MLClient, MLClientManager
from mlclient import _utils as utils
from mlclient.connection import SSLConfig
from mlclient.exceptions import WrongParametersError


def setup_logger():
    """Set up MLClient logging configuration."""
    with utils.get_resource("logging.yaml") as config_file:
        config = yaml.safe_load(config_file.read())
        logging.config.dictConfig(config)


_ML_LOG_LEVELS = {
    logging.CRITICAL: "critical",
    logging.ERROR: "error",
    logging.WARNING: "warning",
    logging.INFO: "info",
    logging.DEBUG: "debug",
    logging.DEBUG - 1: "fine",
}

_LOG_QUERY = (
    "declare variable $message external;\n"
    "declare variable $level external;\n"
    "xdmp:log($message, $level)"
)

_SHUTDOWN = object()


class MLLogHandler(logging.Handler):
    """A logging handler that writes records to a MarkLogic server's error log.

    Records are formatted and forwarded by evaluating ``xdmp:log`` on the server,
    so the same message that reaches other handlers also lands in MarkLogic's
    error log. The server prepends its own timestamp and renders the level, so
    the attached formatter should omit the date and the level name.

    Forwarding is non-blocking: ``emit`` enqueues the record and returns, while a
    single background daemon thread owns one client and sends records in order.
    Records emitted on that worker thread are dropped, so the client's own logging
    cannot feed itself back into the queue.

    Two connection modes are mutually exclusive. Passing ``environment`` loads a
    named ``.mlclient`` environment; otherwise the plain connection details build
    a client directly. Providing ``ssl`` forces HTTPS.

    Parameters
    ----------
    environment : str | None, default None
        A named ``.mlclient`` environment. When set, no connection detail may be
        passed.
    app_server : str | None, default None
        A REST App Server identifier within the environment. None selects the
        first REST server. Ignored outside environment mode.
    host : str, default "localhost"
        A host name, in connection-details mode.
    port : int, default 8000
        A REST App Server port, in connection-details mode.
    protocol : str, default "http"
        A protocol (http / https), in connection-details mode.
    username : str, default "admin"
        A username, in connection-details mode.
    password : str, default "admin"
        A password, in connection-details mode.
    auth : str, default "digest"
        An authentication method, in connection-details mode.
    ssl : dict | SSLConfig | None, default None
        SSL settings (``verify``, ``cert_file``, ``key_file``, ``key_password``).
        A mapping is converted to an SSLConfig. Any value forces HTTPS.
    level : int | str, default logging.NOTSET
        The handler's threshold level.

    Raises
    ------
    WrongParametersError
        If ``environment`` is combined with any connection detail.
    """

    def __init__(
        self,
        environment: str | None = None,
        *,
        app_server: str | None = None,
        host=None,
        port=None,
        protocol=None,
        username=None,
        password=None,
        auth=None,
        ssl=None,
        level: int | str = logging.NOTSET,
    ):
        """Validate the connection choice and prepare a lazily started worker.

        The background thread is not started here; it starts on the first record
        so constructing a handler opens no connection.
        """
        super().__init__(level)
        connection_details = (host, port, protocol, username, password, auth, ssl)
        has_details = any(arg is not None for arg in connection_details)
        if environment is not None and has_details:
            msg = "Pass either an environment or connection details, not both."
            raise WrongParametersError(msg)
        self._environment = environment
        self._app_server = app_server
        self._client_kwargs = _client_kwargs(
            host, port, protocol, username, password, auth, ssl,
        )
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._worker: threading.Thread | None = None
        self._worker_lock = threading.Lock()

    def emit(self, record: logging.LogRecord):
        """Enqueue a formatted record for background forwarding.

        Records emitted on the worker thread are the client's own logging while
        it sends; dropping them breaks the forward-triggers-a-log feedback loop.

        Parameters
        ----------
        record : logging.LogRecord
            The record to forward. Formatting happens here so it runs on the
            calling thread, consistent with other handlers.
        """
        if threading.current_thread() is self._worker:
            return
        self._ensure_worker()
        try:
            item = (record, self.format(record), _ml_log_level(record.levelno))
            self._queue.put(item)
        except Exception:
            self.handleError(record)

    def close(self):
        """Flush the queue and stop the worker before closing the handler.

        Signals the worker to drain remaining records, then joins it so records
        emitted before shutdown are not lost.
        """
        if self._worker is not None:
            self._queue.put(_SHUTDOWN)
            self._worker.join(timeout=5)
        super().close()

    def _ensure_worker(self):
        """Start the forwarding thread once, on first use."""
        with self._worker_lock:
            if self._worker is None:
                self._worker = threading.Thread(
                    target=self._forward_records,
                    name="MLLogHandler",
                    daemon=True,
                )
                self._worker.start()

    def _forward_records(self):
        """Own one client and forward queued records until shutdown."""
        with self._create_client() as client:
            for record, message, level in iter(self._queue.get, _SHUTDOWN):
                self._send(client, record, message, level)

    def _send(
        self,
        client: MLClient,
        record: logging.LogRecord,
        message: str,
        level: str,
    ):
        """Write one record to the server, reporting a failed send.

        Parameters
        ----------
        client : MLClient
            The connected client owned by the worker thread.
        record : logging.LogRecord
            The originating record, used for error reporting.
        message : str
            The already-formatted message.
        level : str
            The MarkLogic log level.
        """
        try:
            variables = {"message": message, "level": level}
            client.eval.xquery(_LOG_QUERY, variables=variables)
        except Exception:
            self.handleError(record)

    def _create_client(self) -> MLClient:
        """Build the client for the configured connection mode.

        Returns
        -------
        MLClient
            A client from the named environment, or one built from connection
            details.
        """
        if self._environment is not None:
            return MLClientManager(self._environment).get_client(self._app_server)
        return MLClient(**self._client_kwargs)


def setup_ml_logger(
    config,
    *,
    environment=None,
    app_server=None,
    handler_id="marklogic",
):
    """Apply a logging config, injecting the MarkLogic handler's connection.

    Keeps the handler definition declarative in a dictConfig document while the
    environment and app server come from code.

    Parameters
    ----------
    config : dict | str | pathlib.Path
        A dictConfig mapping, or a path to a YAML file holding one.
    environment : str | None, default None
        An environment injected into the handler when given.
    app_server : str | None, default None
        An app server injected into the handler when given.
    handler_id : str, default "marklogic"
        The handler entry to inject into.
    """
    config = _load_config(config)
    handler = config["handlers"][handler_id]
    if environment is not None:
        handler["environment"] = environment
    if app_server is not None:
        handler["app_server"] = app_server
    logging.config.dictConfig(config)


def _client_kwargs(host, port, protocol, username, password, auth, ssl) -> dict:
    """Collect MLClient keyword arguments from set connection details.

    Unset details are omitted so MLClient applies its own defaults. An SSL
    mapping becomes an SSLConfig and forces HTTPS.

    Returns
    -------
    dict
        Keyword arguments for MLClient.
    """
    details = {
        "host": host,
        "port": port,
        "protocol": protocol,
        "username": username,
        "password": password,
        "auth": auth,
    }
    kwargs = {name: value for name, value in details.items() if value is not None}
    if ssl is not None:
        kwargs["ssl"] = ssl if isinstance(ssl, SSLConfig) else SSLConfig(**ssl)
        kwargs.setdefault("protocol", "https")
    return kwargs


def _ml_log_level(levelno: int) -> str:
    """Map a Python level number to a MarkLogic log level.

    Parameters
    ----------
    levelno : int
        A Python logging level number.

    Returns
    -------
    str
        The nearest defined MarkLogic level at or below the number, flooring at
        "fine".
    """
    candidates = [level for level in _ML_LOG_LEVELS if level <= levelno]
    return _ML_LOG_LEVELS[max(candidates)] if candidates else "fine"


def _load_config(config):
    """Return a dictConfig mapping from a dict or a YAML file path.

    A dict is deep-copied so the caller's object is not mutated.

    Parameters
    ----------
    config : dict | str | pathlib.Path
        A dictConfig mapping or a path to a YAML file.

    Returns
    -------
    dict
        A mapping ready for logging.config.dictConfig.
    """
    if isinstance(config, dict):
        return deepcopy(config)
    with Path(config).open() as config_file:
        return yaml.safe_load(config_file)


__all__ = ["MLLogHandler", "setup_logger", "setup_ml_logger"]
