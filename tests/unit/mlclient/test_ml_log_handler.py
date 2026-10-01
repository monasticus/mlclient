import logging
import threading
from unittest.mock import MagicMock

import pytest

from mlclient.connection import SSLConfig
from mlclient.exceptions import WrongParametersError
from mlclient.logging import (
    MLLogHandler,
    setup_ml_logger,
)
from mlclient.logging import (
    _client_kwargs,
    _load_config,
    _ml_log_level,
)


def _record(name="app", level=logging.INFO, message="hello"):
    return logging.LogRecord(name, level, __file__, 1, message, None, None)


def _mock_client():
    client = MagicMock()
    client.__enter__.return_value = client
    return client


def test_emit_does_not_block_and_worker_forwards_record(mocker):
    client = _mock_client()
    handler = MLLogHandler(host="example", port=8010)
    mocker.patch.object(handler, "_create_client", return_value=client)

    handler.emit(_record(message="first"))
    handler.emit(_record(message="second"))
    handler.close()

    assert client.eval.xquery.call_count == 2
    first_call = client.eval.xquery.call_args_list[0]
    assert first_call.args[0] == (
        "declare variable $message external;\n"
        "declare variable $level external;\n"
        "xdmp:log($message, $level)"
    )
    assert first_call.kwargs["variables"] == {"message": "first", "level": "info"}


def test_emit_starts_worker_only_once(mocker):
    handler = MLLogHandler(host="example")
    mocker.patch.object(handler, "_create_client", return_value=_mock_client())

    handler.emit(_record())
    worker = handler._worker
    handler.emit(_record())
    assert handler._worker is worker

    handler.close()


def test_send_failure_reports_error_and_worker_survives(mocker):
    client = _mock_client()
    client.eval.xquery.side_effect = RuntimeError("boom")
    handler = MLLogHandler(host="example")
    mocker.patch.object(handler, "_create_client", return_value=client)
    handle_error = mocker.patch.object(handler, "handleError")

    record = _record()
    handler.emit(record)
    handler.close()

    handle_error.assert_called_once_with(record)


def test_emit_reports_error_when_enqueue_fails(mocker):
    handler = MLLogHandler(host="example")
    mocker.patch.object(handler, "_ensure_worker")
    handler._queue = MagicMock()
    handler._queue.put.side_effect = RuntimeError("full")
    handle_error = mocker.patch.object(handler, "handleError")

    record = _record()
    handler.emit(record)

    handle_error.assert_called_once_with(record)


def test_emit_drops_records_produced_while_forwarding(mocker):
    handler = MLLogHandler(host="example")
    ensure = mocker.patch.object(handler, "_ensure_worker")
    handler._queue = MagicMock()
    handler._worker = threading.current_thread()

    handler.emit(_record())

    handler._queue.put.assert_not_called()
    ensure.assert_not_called()


@pytest.mark.parametrize(
    ("levelno", "expected"),
    [
        (logging.CRITICAL, "critical"),
        (logging.ERROR, "error"),
        (logging.WARNING, "warning"),
        (logging.INFO, "info"),
        (logging.DEBUG, "debug"),
        (logging.DEBUG - 1, "fine"),
        (45, "error"),
        (35, "warning"),
        (25, "info"),
        (15, "debug"),
        (60, "critical"),
        (5, "fine"),
    ],
)
def test_level_mapping(levelno, expected):
    assert _ml_log_level(levelno) == expected


def test_environment_and_connection_details_conflict():
    with pytest.raises(WrongParametersError):
        MLLogHandler("local", host="example")


def test_create_client_uses_environment(mocker):
    manager = mocker.patch("mlclient.logging.MLClientManager")
    handler = MLLogHandler("local", app_server="content")

    handler._create_client()

    manager.assert_called_once_with("local")
    manager.return_value.get_client.assert_called_once_with("content")


def test_create_client_uses_connection_details(mocker):
    client_cls = mocker.patch("mlclient.logging.MLClient")
    handler = MLLogHandler(host="example", port=8010, auth="basic")

    handler._create_client()

    client_cls.assert_called_once_with(host="example", port=8010, auth="basic")


def test_close_without_emit_closes_cleanly():
    handler = MLLogHandler(host="example")
    handler.close()
    assert handler._worker is None


def test_client_kwargs_omits_unset_details():
    assert _client_kwargs(None, None, None, None, None, None, None) == {}


def test_client_kwargs_keeps_set_details():
    kwargs = _client_kwargs("host", 8010, None, "user", None, None, None)
    assert kwargs == {"host": "host", "port": 8010, "username": "user"}


def test_client_kwargs_converts_ssl_mapping_and_forces_https():
    kwargs = _client_kwargs(None, None, None, None, None, None, {"verify": False})
    assert kwargs["protocol"] == "https"
    assert isinstance(kwargs["ssl"], SSLConfig)
    assert kwargs["ssl"].verify is False


def test_client_kwargs_passes_ssl_config_through():
    ssl = SSLConfig(verify=True)
    kwargs = _client_kwargs(None, None, None, None, None, None, ssl)
    assert kwargs["ssl"] is ssl


def test_setup_ml_logger_injects_environment_and_app_server(mocker):
    dict_config = mocker.patch("logging.config.dictConfig")
    config = {"version": 1, "handlers": {"marklogic": {}}}

    setup_ml_logger(config, environment="local", app_server="content")

    applied = dict_config.call_args.args[0]
    assert applied["handlers"]["marklogic"] == {
        "environment": "local",
        "app_server": "content",
    }
    assert config["handlers"]["marklogic"] == {}


def test_setup_ml_logger_leaves_handler_untouched_without_overrides(mocker):
    dict_config = mocker.patch("logging.config.dictConfig")
    config = {"version": 1, "handlers": {"ml": {"class": "x"}}}

    setup_ml_logger(config, handler_id="ml")

    assert dict_config.call_args.args[0]["handlers"]["ml"] == {"class": "x"}


def test_setup_ml_logger_reads_yaml_file(tmp_path, mocker):
    dict_config = mocker.patch("logging.config.dictConfig")
    config_file = tmp_path / "logging.yaml"
    config_file.write_text("version: 1\nhandlers:\n  marklogic: {}\n")

    setup_ml_logger(config_file, environment="local")

    assert dict_config.call_args.args[0]["handlers"]["marklogic"] == {
        "environment": "local",
    }


def test_load_config_deep_copies_mapping():
    config = {"handlers": {"marklogic": {}}}
    loaded = _load_config(config)
    loaded["handlers"]["marklogic"]["environment"] = "local"
    assert config["handlers"]["marklogic"] == {}
