import logging
import threading
from unittest.mock import MagicMock

import pytest

from mlclient.connection import SSLConfig
from mlclient.exceptions import WrongParametersError
from mlclient.logging import MLLogHandler, setup_ml_logger


def make_record(name="app", level=logging.INFO, message="hello"):
    return logging.LogRecord(name, level, __file__, 1, message, None, None)


def make_mock_client():
    client = MagicMock()
    client.__enter__.return_value = client
    return client


def test_emit_forwards_records_in_order(mocker):
    client = make_mock_client()
    client_cls = mocker.patch("mlclient.logging.MLClient", return_value=client)
    handler = MLLogHandler(host="example", port=8010)

    handler.emit(make_record(message="first"))
    handler.emit(make_record(message="second"))
    handler.close()

    client_cls.assert_called_once_with(host="example", port=8010)
    assert client.eval.xquery.call_count == 2
    first_call = client.eval.xquery.call_args_list[0]
    assert first_call.args[0] == (
        "declare variable $message external;\n"
        "declare variable $level external;\n"
        "xdmp:log($message, $level)"
    )
    assert first_call.kwargs["variables"] == {"message": "first", "level": "info"}


def test_emit_reuses_one_client(mocker):
    client = make_mock_client()
    client_cls = mocker.patch("mlclient.logging.MLClient", return_value=client)
    handler = MLLogHandler(host="example")

    handler.emit(make_record())
    handler.emit(make_record())
    handler.close()

    client_cls.assert_called_once_with(host="example")


def test_send_failure_reports_error_and_worker_survives(mocker):
    client = make_mock_client()
    client.eval.xquery.side_effect = [RuntimeError("boom"), None]
    mocker.patch("mlclient.logging.MLClient", return_value=client)
    handler = MLLogHandler(host="example")
    handle_error = mocker.patch.object(handler, "handleError")

    first = make_record(message="first")
    handler.emit(first)
    handler.emit(make_record(message="second"))
    handler.close()

    handle_error.assert_called_once_with(first)
    assert client.eval.xquery.call_count == 2


def test_client_creation_failure_reports_error_and_retries(mocker):
    client = make_mock_client()
    mocker.patch(
        "mlclient.logging.MLClient",
        side_effect=[RuntimeError("boom"), client],
    )
    handler = MLLogHandler(host="example")
    handle_error = mocker.patch.object(handler, "handleError")

    first = make_record(message="first")
    handler.emit(first)
    handler.emit(make_record(message="second"))
    handler.close()

    handle_error.assert_called_once_with(first)
    client.eval.xquery.assert_called_once()
    assert client.eval.xquery.call_args.kwargs["variables"]["message"] == "second"


def test_format_failure_reports_error(mocker):
    formatter = mocker.Mock()
    formatter.format.side_effect = RuntimeError("boom")
    handler = MLLogHandler(host="example")
    handler.setFormatter(formatter)
    handle_error = mocker.patch.object(handler, "handleError")

    record = make_record()
    handler.emit(record)
    handler.close()

    handle_error.assert_called_once_with(record)


def test_records_produced_while_forwarding_are_dropped(mocker):
    client = make_mock_client()
    logger = logging.getLogger("forwarding-loop-test")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = MLLogHandler(host="example")
    logger.addHandler(handler)

    def log_recursively(*_args, **_kwargs):
        logger.info("recursive")

    client.eval.xquery.side_effect = log_recursively
    mocker.patch("mlclient.logging.MLClient", return_value=client)

    logger.warning("original")
    handler.close()
    logger.removeHandler(handler)

    client.eval.xquery.assert_called_once()


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
def test_level_mapping(levelno, expected, mocker):
    client = make_mock_client()
    mocker.patch("mlclient.logging.MLClient", return_value=client)
    handler = MLLogHandler(host="example")

    handler.emit(make_record(level=levelno))
    handler.close()

    assert client.eval.xquery.call_args.kwargs["variables"]["level"] == expected


def test_environment_and_connection_details_conflict():
    with pytest.raises(WrongParametersError):
        MLLogHandler("local", host="example")


def test_environment_selects_app_server(mocker):
    client = make_mock_client()
    manager = mocker.patch("mlclient.logging.MLClientManager")
    manager.return_value.get_client.return_value = client
    handler = MLLogHandler("local", app_server="content")

    handler.emit(make_record())
    handler.close()

    manager.assert_called_once_with("local")
    manager.return_value.get_client.assert_called_once_with("content")


def test_connection_details_are_forwarded(mocker):
    client = make_mock_client()
    client_cls = mocker.patch("mlclient.logging.MLClient", return_value=client)
    handler = MLLogHandler(host="example", port=8010, auth="basic")

    handler.emit(make_record())
    handler.close()

    client_cls.assert_called_once_with(host="example", port=8010, auth="basic")


def test_close_without_emit_closes_cleanly():
    MLLogHandler(host="example").close()


def test_close_waits_for_worker_to_flush(mocker):
    entered = threading.Event()
    release = threading.Event()
    client = make_mock_client()

    def block_send(*_args, **_kwargs):
        entered.set()
        release.wait()

    client.eval.xquery.side_effect = block_send
    mocker.patch("mlclient.logging.MLClient", return_value=client)
    handler = MLLogHandler(host="example")
    handler.emit(make_record())
    assert entered.wait(timeout=1)

    closer = threading.Thread(target=handler.close)
    closer.start()
    assert closer.is_alive()
    release.set()
    closer.join(timeout=1)

    assert not closer.is_alive()


def test_unset_connection_details_use_client_defaults(mocker):
    client = make_mock_client()
    client_cls = mocker.patch("mlclient.logging.MLClient", return_value=client)
    handler = MLLogHandler()

    handler.emit(make_record())
    handler.close()

    client_cls.assert_called_once_with()


def test_ssl_mapping_forces_https(mocker):
    client = make_mock_client()
    client_cls = mocker.patch("mlclient.logging.MLClient", return_value=client)
    handler = MLLogHandler(ssl={"verify": False})

    handler.emit(make_record())
    handler.close()

    kwargs = client_cls.call_args.kwargs
    assert kwargs["protocol"] == "https"
    assert isinstance(kwargs["ssl"], SSLConfig)
    assert kwargs["ssl"].verify is False


def test_ssl_config_is_forwarded(mocker):
    client = make_mock_client()
    client_cls = mocker.patch("mlclient.logging.MLClient", return_value=client)
    ssl = SSLConfig(verify=True)
    handler = MLLogHandler(ssl=ssl)

    handler.emit(make_record())
    handler.close()

    assert client_cls.call_args.kwargs["ssl"] is ssl


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
