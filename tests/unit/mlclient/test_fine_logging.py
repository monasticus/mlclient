import logging

import pytest

from mlclient._logging import register_fine_logging


def test_register_fine_logging(monkeypatch, caplog):
    monkeypatch.delattr(logging, "FINE")
    monkeypatch.delattr(logging, "fine")
    monkeypatch.delattr(logging.Logger, "fine")
    register_fine_logging()
    with caplog.at_level(logging.FINE):
        logging.getLogger(__name__).fine("Document %s", "example", extra={"uri": "/x"})
        logging.fine("Root message")
    assert logging.FINE == logging.DEBUG - 1
    assert logging.getLevelName(logging.FINE) == "FINE"
    assert [record.getMessage() for record in caplog.records] == [
        "Document example",
        "Root message",
    ]
    assert caplog.records[0].uri == "/x"
    assert all(
        record.funcName == "test_register_fine_logging" for record in caplog.records
    )


def test_register_fine_logging_keeps_existing_methods():
    logger_method = logging.Logger.fine
    root_method = logging.fine
    register_fine_logging()
    assert logging.Logger.fine is logger_method
    assert logging.fine is root_method


def test_fine_respects_log_level(caplog):
    with caplog.at_level(logging.DEBUG):
        logging.getLogger(__name__).fine("Not visible")
        logging.fine("Not visible either")
    assert not caplog.records


def test_fine_forwards_exception_and_stacklevel(caplog):
    def log_failure():
        try:
            int("example")
        except ValueError:
            logging.getLogger(__name__).fine("Failed", exc_info=True, stacklevel=2)

    with caplog.at_level(logging.FINE):
        log_failure()
    assert caplog.records[0].exc_info[0] is ValueError
    assert caplog.records[0].funcName == "test_fine_forwards_exception_and_stacklevel"


def test_root_fine_configures_missing_handlers(monkeypatch, mocker):
    monkeypatch.setattr(logging.getLogger(), "handlers", [])
    configure = mocker.patch("logging.basicConfig")
    logging.fine("Below default threshold")
    configure.assert_called_once_with()


@pytest.mark.parametrize("use_root", [False, True])
@pytest.mark.parametrize(
    "exc_info",
    [
        None,
        False,
        ValueError("failure"),
        (ValueError, ValueError("failure"), None),
        (None, None, None),
    ],
)
def test_fine_forwards_standard_logging_options(caplog, use_root, exc_info):
    emit = logging.fine if use_root else logging.getLogger(__name__).fine
    with caplog.at_level(logging.FINE):
        emit(
            "Document %s",
            "example",
            exc_info=exc_info,
            extra={"uri": "/example.xml"},
            stack_info=True,
            stacklevel=1,
        )
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.getMessage() == "Document example"
    assert record.uri == "/example.xml"
    assert record.funcName == "test_fine_forwards_standard_logging_options"
    assert record.stack_info.startswith("Stack (most recent call last):")
    if isinstance(exc_info, BaseException):
        assert record.exc_info == (type(exc_info), exc_info, exc_info.__traceback__)
    else:
        assert record.exc_info == exc_info
