from copy import copy

from mlclient.jobs import DocumentJobReport
from mlclient.jobs.documents_jobs import DocumentReport, DocumentStatus


def test_add_doc_report():
    report = DocumentJobReport()
    assert report.pending == 0
    assert report.completed == 0
    assert report.successful == 0
    assert report.failed == 0
    assert report.pending_docs == []
    assert report.successful_docs == []
    assert report.failed_docs == []

    report.add_doc_report(
        DocumentReport(
            uri="/some/uri-1.xml",
            status="PENDING",
        ),
    )
    assert report.pending == 1
    assert report.completed == 0
    assert report.successful == 0
    assert report.failed == 0
    assert report.pending_docs == ["/some/uri-1.xml"]
    assert report.successful_docs == []
    assert report.failed_docs == []

    report.add_doc_report(
        DocumentReport(
            uri="/some/uri-2.xml",
            status="PENDING",
        ),
    )
    assert report.pending == 2
    assert report.completed == 0
    assert report.successful == 0
    assert report.failed == 0
    assert report.pending_docs == ["/some/uri-1.xml", "/some/uri-2.xml"]
    assert report.successful_docs == []
    assert report.failed_docs == []

    report.add_doc_report(
        DocumentReport(
            uri="/some/uri-1.xml",
            status="SUCCESS",
        ),
    )
    assert report.pending == 1
    assert report.completed == 1
    assert report.successful == 1
    assert report.failed == 0
    assert report.pending_docs == ["/some/uri-2.xml"]
    assert report.successful_docs == ["/some/uri-1.xml"]
    assert report.failed_docs == []

    report.add_doc_report(
        DocumentReport(
            uri="/some/uri-2.xml",
            status="FAILURE",
        ),
    )
    assert report.pending == 0
    assert report.completed == 2
    assert report.successful == 1
    assert report.failed == 1
    assert report.pending_docs == []
    assert report.successful_docs == ["/some/uri-1.xml"]
    assert report.failed_docs == ["/some/uri-2.xml"]

    report.add_doc_report(
        DocumentReport(
            uri="/some/uri-3.xml",
            status="SUCCESS",
        ),
    )
    assert report.pending == 0
    assert report.completed == 3
    assert report.successful == 2
    assert report.failed == 1
    assert report.pending_docs == []
    assert report.successful_docs == ["/some/uri-1.xml", "/some/uri-3.xml"]
    assert report.failed_docs == ["/some/uri-2.xml"]


def test_add_doc():
    report = DocumentJobReport()
    assert report.pending == 0
    assert report.completed == 0
    assert report.successful == 0
    assert report.failed == 0
    assert report.pending_docs == []
    assert report.successful_docs == []
    assert report.failed_docs == []

    report.add_pending_doc("/some/uri-1.xml")
    assert report.pending == 1
    assert report.completed == 0
    assert report.successful == 0
    assert report.failed == 0
    assert report.pending_docs == ["/some/uri-1.xml"]
    assert report.successful_docs == []
    assert report.failed_docs == []

    report.add_pending_doc("/some/uri-2.xml")
    assert report.pending == 2
    assert report.completed == 0
    assert report.successful == 0
    assert report.failed == 0
    assert report.pending_docs == ["/some/uri-1.xml", "/some/uri-2.xml"]
    assert report.successful_docs == []
    assert report.failed_docs == []

    report.add_successful_doc("/some/uri-1.xml")
    assert report.pending == 1
    assert report.completed == 1
    assert report.successful == 1
    assert report.failed == 0
    assert report.pending_docs == ["/some/uri-2.xml"]
    assert report.successful_docs == ["/some/uri-1.xml"]
    assert report.failed_docs == []

    report.add_failed_doc("/some/uri-2.xml", RuntimeError("Some error"))
    assert report.pending == 0
    assert report.completed == 2
    assert report.successful == 1
    assert report.failed == 1
    assert report.pending_docs == []
    assert report.successful_docs == ["/some/uri-1.xml"]
    assert report.failed_docs == ["/some/uri-2.xml"]

    report.add_successful_doc("/some/uri-3.xml")
    assert report.pending == 0
    assert report.completed == 3
    assert report.successful == 2
    assert report.failed == 1
    assert report.pending_docs == []
    assert report.successful_docs == ["/some/uri-1.xml", "/some/uri-3.xml"]
    assert report.failed_docs == ["/some/uri-2.xml"]


def test_add_docs():
    report = DocumentJobReport()
    assert report.pending == 0
    assert report.completed == 0
    assert report.successful == 0
    assert report.failed == 0
    assert report.pending_docs == []
    assert report.successful_docs == []
    assert report.failed_docs == []

    report.add_pending_docs(["/some/uri-1.xml", "/some/uri-2.xml"])
    assert report.pending == 2
    assert report.completed == 0
    assert report.successful == 0
    assert report.failed == 0
    assert report.pending_docs == ["/some/uri-1.xml", "/some/uri-2.xml"]
    assert report.successful_docs == []
    assert report.failed_docs == []

    report.add_successful_docs(["/some/uri-1.xml", "/some/uri-3.xml"])
    assert report.pending == 1
    assert report.completed == 2
    assert report.successful == 2
    assert report.failed == 0
    assert report.pending_docs == ["/some/uri-2.xml"]
    assert report.successful_docs == ["/some/uri-1.xml", "/some/uri-3.xml"]
    assert report.failed_docs == []

    report.add_failed_docs(
        ["/some/uri-2.xml", "/some/uri-4.xml"],
        RuntimeError("Some error"),
    )
    assert report.pending == 0
    assert report.completed == 4
    assert report.successful == 2
    assert report.failed == 2
    assert report.pending_docs == []
    assert report.successful_docs == ["/some/uri-1.xml", "/some/uri-3.xml"]
    assert report.failed_docs == ["/some/uri-2.xml", "/some/uri-4.xml"]

    report.add_successful_docs(["/some/uri-5.xml"])
    assert report.pending == 0
    assert report.completed == 5
    assert report.successful == 3
    assert report.failed == 2
    assert report.pending_docs == []
    assert report.successful_docs == [
        "/some/uri-1.xml",
        "/some/uri-3.xml",
        "/some/uri-5.xml",
    ]
    assert report.failed_docs == ["/some/uri-2.xml", "/some/uri-4.xml"]


def test_get_doc_report_non_existing():
    report = DocumentJobReport()

    doc_report = report.get_doc_report("/some/uri-1.xml")
    assert doc_report is None


def test_get_doc_report_pending():
    report = DocumentJobReport()
    report.add_pending_doc("/some/uri-1.xml")

    doc_report = report.get_doc_report("/some/uri-1.xml")
    assert doc_report.uri == "/some/uri-1.xml"
    assert doc_report.status == DocumentStatus.pending
    assert doc_report.details is None


def test_get_doc_report_successful():
    report = DocumentJobReport()
    report.add_successful_doc("/some/uri-1.xml")

    doc_report = report.get_doc_report("/some/uri-1.xml")
    assert doc_report.uri == "/some/uri-1.xml"
    assert doc_report.status == DocumentStatus.success
    assert doc_report.details is None


def test_get_doc_report_failed():
    report = DocumentJobReport()
    report.add_failed_doc("/some/uri-1.xml", RuntimeError("Some error"))

    doc_report = report.get_doc_report("/some/uri-1.xml")
    assert doc_report.uri == "/some/uri-1.xml"
    assert doc_report.status == DocumentStatus.failure
    assert doc_report.details.error == RuntimeError
    assert doc_report.details.message == "Some error"


def test_full_report_encapsulation():
    report = DocumentJobReport()
    report.add_successful_doc("/some/uri-1.xml")
    assert report.successful == 1
    assert report.failed == 0
    assert report.full["/some/uri-1.xml"].status == DocumentStatus.success

    report.full["/some/uri-1.xml"].status = DocumentStatus.failure

    assert report.successful == 1
    assert report.failed == 0
    assert report.full["/some/uri-1.xml"].status == DocumentStatus.success


def test_copy():
    report = DocumentJobReport()
    report.add_successful_doc("/some/uri-1.xml")
    assert report.successful == 1

    report_copy = copy(report)
    report_copy.add_successful_doc("/some/uri-2.xml")
    assert report_copy.successful == 2

    assert report.successful == 1
