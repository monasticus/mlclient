from mlclient.jobs import DocumentJobReport
from mlclient.jobs.documents_jobs import DocumentReport


def test_add_doc_report():
    status = DocumentJobReport()
    assert status.pending == 0
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.pending_docs == []
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_doc_report(
        DocumentReport(
            uri="/some/uri-1.xml",
            status="PENDING",
        ),
    )
    assert status.pending == 1
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.pending_docs == ["/some/uri-1.xml"]
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_doc_report(
        DocumentReport(
            uri="/some/uri-2.xml",
            status="PENDING",
        ),
    )
    assert status.pending == 2
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.pending_docs == ["/some/uri-1.xml", "/some/uri-2.xml"]
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_doc_report(
        DocumentReport(
            uri="/some/uri-1.xml",
            status="SUCCESS",
        ),
    )
    assert status.pending == 1
    assert status.completed == 1
    assert status.successful == 1
    assert status.failed == 0
    assert status.pending_docs == ["/some/uri-2.xml"]
    assert status.successful_docs == ["/some/uri-1.xml"]
    assert status.failed_docs == []

    status.add_doc_report(
        DocumentReport(
            uri="/some/uri-2.xml",
            status="FAILURE",
        ),
    )
    assert status.pending == 0
    assert status.completed == 2
    assert status.successful == 1
    assert status.failed == 1
    assert status.pending_docs == []
    assert status.successful_docs == ["/some/uri-1.xml"]
    assert status.failed_docs == ["/some/uri-2.xml"]

    status.add_doc_report(
        DocumentReport(
            uri="/some/uri-3.xml",
            status="SUCCESS",
        ),
    )
    assert status.pending == 0
    assert status.completed == 3
    assert status.successful == 2
    assert status.failed == 1
    assert status.pending_docs == []
    assert status.successful_docs == ["/some/uri-1.xml", "/some/uri-3.xml"]
    assert status.failed_docs == ["/some/uri-2.xml"]


def test_add_doc():
    status = DocumentJobReport()
    assert status.pending == 0
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.pending_docs == []
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_pending_doc("/some/uri-1.xml")
    assert status.pending == 1
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.pending_docs == ["/some/uri-1.xml"]
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_pending_doc("/some/uri-2.xml")
    assert status.pending == 2
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.pending_docs == ["/some/uri-1.xml", "/some/uri-2.xml"]
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_successful_doc("/some/uri-1.xml")
    assert status.pending == 1
    assert status.completed == 1
    assert status.successful == 1
    assert status.failed == 0
    assert status.pending_docs == ["/some/uri-2.xml"]
    assert status.successful_docs == ["/some/uri-1.xml"]
    assert status.failed_docs == []

    status.add_failed_doc("/some/uri-2.xml", Exception("Some error"))
    assert status.pending == 0
    assert status.completed == 2
    assert status.successful == 1
    assert status.failed == 1
    assert status.pending_docs == []
    assert status.successful_docs == ["/some/uri-1.xml"]
    assert status.failed_docs == ["/some/uri-2.xml"]

    status.add_successful_doc("/some/uri-3.xml")
    assert status.pending == 0
    assert status.completed == 3
    assert status.successful == 2
    assert status.failed == 1
    assert status.pending_docs == []
    assert status.successful_docs == ["/some/uri-1.xml", "/some/uri-3.xml"]
    assert status.failed_docs == ["/some/uri-2.xml"]


def test_add_docs():
    status = DocumentJobReport()
    assert status.pending == 0
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.pending_docs == []
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_pending_docs(["/some/uri-1.xml", "/some/uri-2.xml"])
    assert status.pending == 2
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.pending_docs == ["/some/uri-1.xml", "/some/uri-2.xml"]
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_successful_docs(["/some/uri-1.xml", "/some/uri-3.xml"])
    assert status.pending == 1
    assert status.completed == 2
    assert status.successful == 2
    assert status.failed == 0
    assert status.pending_docs == ["/some/uri-2.xml"]
    assert status.successful_docs == ["/some/uri-1.xml", "/some/uri-3.xml"]
    assert status.failed_docs == []

    status.add_failed_docs(
        ["/some/uri-2.xml", "/some/uri-4.xml"],
        Exception("Some error"),
    )
    assert status.pending == 0
    assert status.completed == 4
    assert status.successful == 2
    assert status.failed == 2
    assert status.pending_docs == []
    assert status.successful_docs == ["/some/uri-1.xml", "/some/uri-3.xml"]
    assert status.failed_docs == ["/some/uri-2.xml", "/some/uri-4.xml"]

    status.add_successful_docs(["/some/uri-5.xml"])
    assert status.pending == 0
    assert status.completed == 5
    assert status.successful == 3
    assert status.failed == 2
    assert status.pending_docs == []
    assert status.successful_docs == [
        "/some/uri-1.xml",
        "/some/uri-3.xml",
        "/some/uri-5.xml",
    ]
    assert status.failed_docs == ["/some/uri-2.xml", "/some/uri-4.xml"]
