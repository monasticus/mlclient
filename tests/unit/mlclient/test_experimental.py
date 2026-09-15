import inspect
import logging

from mlclient._experimental import experimental
from mlclient.jobs import DocumentJobReport, DocumentStatus, ReadDocumentsJob


def test_marker_preserves_class_identity_and_constructor_signature(caplog):
    class Example:
        def __init__(self, value: int = 3):
            self.value = value

    signature = inspect.signature(Example)
    with caplog.at_level(logging.WARNING):
        decorated = experimental(log_on_init=True)(Example)
        assert decorated is Example
        assert inspect.signature(decorated) == signature
        assert decorated(value=7).value == 7
    assert len(caplog.records) == 1
    assert "Example is experimental" in caplog.text
    assert "experimental" in decorated.__doc__


def test_reports_and_enums_are_marked_without_per_instance_warnings(caplog):
    with caplog.at_level(logging.WARNING):
        report = DocumentJobReport()
        status = next(iter(DocumentStatus))
    assert report.__experimental__ == status.__experimental__
    assert not caplog.records
    assert ReadDocumentsJob.__experimental__ == report.__experimental__
