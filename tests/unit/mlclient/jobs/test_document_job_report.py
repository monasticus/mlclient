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
            report="PENDING",
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
            report="PENDING",
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
            report="SUCCESS",
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
            report="FAILURE",
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
            report="SUCCESS",
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

    report.add_failed_doc("/some/uri-2.xml", Exception("Some error"))
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
        Exception("Some error"),
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
