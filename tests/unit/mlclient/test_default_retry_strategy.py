from __future__ import annotations

import contextlib
import socket
import socketserver
import struct
import threading
import time

import httpx
import pytest
from httpx_retries import Retry

from mlclient.clients import HttpClient
from mlclient.http import DEFAULT_RETRY_STRATEGY

ATTEMPTS_WITH_ALL_RETRIES = DEFAULT_RETRY_STRATEGY.total + 1


@pytest.fixture(autouse=True)
def _no_backoff(mocker):
    mocker.patch.object(Retry, "sleep")


class _RequestCountingServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, respond):
        super().__init__(("127.0.0.1", 0), _RequestHandler)
        self.respond = respond
        self.requests_received = 0
        self._lock = threading.Lock()

    def count_request(self):
        with self._lock:
            self.requests_received += 1


class _RequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self._read_request_head()
        self.server.count_request()
        self.server.respond(self.request)

    def _read_request_head(self):
        received = b""
        while b"\r\n\r\n" not in received:
            chunk = self.request.recv(4096)
            if not chunk:
                return
            received += chunk


def _reset_connection(connection):
    connection.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_LINGER,
        struct.pack("ii", 1, 0),
    )


def _close_without_response(_connection):
    pass


def _respond_too_late(_connection):
    time.sleep(0.3)


def _respond_with_status(status_code):
    def respond(connection):
        connection.sendall(
            f"HTTP/1.1 {status_code} Status\r\n"
            "Content-Length: 0\r\nConnection: close\r\n\r\n".encode(),
        )

    return respond


def _requests_received_by_get(respond):
    server = _RequestCountingServer(respond)
    threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.01},
        daemon=True,
    ).start()
    try:
        port = server.server_address[1]
        timeout = httpx.Timeout(1.0, read=0.05)
        with (
            HttpClient(host="127.0.0.1", port=port, auth=None, timeout=timeout) as ml,
            contextlib.suppress(httpx.TransportError),
        ):
            ml.get("/v1/search")
        return server.requests_received
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize(
    "respond",
    [_reset_connection, _close_without_response],
    ids=["reset-read-error", "closed-remote-protocol-error"],
)
def test_default_strategy_retries_aborted_connection(respond):
    assert _requests_received_by_get(respond) == ATTEMPTS_WITH_ALL_RETRIES


def test_default_strategy_does_not_retry_read_timeout():
    assert _requests_received_by_get(_respond_too_late) == 1


def test_default_strategy_does_not_retry_gateway_timeout():
    assert _requests_received_by_get(_respond_with_status(504)) == 1


@pytest.mark.parametrize("status_code", [429, 502, 503])
def test_default_strategy_retries_status(status_code):
    respond = _respond_with_status(status_code)

    assert _requests_received_by_get(respond) == ATTEMPTS_WITH_ALL_RETRIES


@pytest.mark.parametrize(
    "exception_type",
    [
        httpx.ConnectError,
        httpx.ConnectTimeout,
        httpx.PoolTimeout,
        httpx.WriteTimeout,
        httpx.WriteError,
        httpx.ReadError,
        httpx.CloseError,
        httpx.RemoteProtocolError,
    ],
)
def test_default_strategy_retries_exception(exception_type):
    assert DEFAULT_RETRY_STRATEGY.is_retryable_exception(exception_type("failed"))


def test_default_strategy_does_not_retry_read_timeout_exception():
    exception = httpx.ReadTimeout("timed out")

    assert not DEFAULT_RETRY_STRATEGY.is_retryable_exception(exception)


def test_default_strategy_never_retries_post():
    assert not DEFAULT_RETRY_STRATEGY.is_retryable_method("POST")
