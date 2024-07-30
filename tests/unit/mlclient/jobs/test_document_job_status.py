from mlclient.jobs import DocumentJobStatus


def test_add_successful_doc():
    status = DocumentJobStatus()
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_successful_doc("/some/uri-1.xml")
    assert status.completed == 1
    assert status.successful == 1
    assert status.failed == 0
    assert status.successful_docs == ["/some/uri-1.xml"]
    assert status.failed_docs == []

    status.add_successful_doc("/some/uri-2.xml")
    assert status.completed == 2
    assert status.successful == 2
    assert status.failed == 0
    assert status.successful_docs == ["/some/uri-1.xml", "/some/uri-2.xml"]
    assert status.failed_docs == []


def test_add_successful_docs():
    status = DocumentJobStatus()
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_successful_docs(["/some/uri-1.xml"])
    assert status.completed == 1
    assert status.successful == 1
    assert status.failed == 0
    assert status.successful_docs == ["/some/uri-1.xml"]
    assert status.failed_docs == []

    status.add_successful_docs(["/some/uri-2.xml", "/some/uri-3.xml"])
    assert status.completed == 3
    assert status.successful == 3
    assert status.failed == 0
    assert status.successful_docs == [
        "/some/uri-1.xml",
        "/some/uri-2.xml",
        "/some/uri-3.xml",
    ]
    assert status.failed_docs == []


def test_add_failed_doc():
    status = DocumentJobStatus()
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_failed_doc("/some/uri-1.xml")
    assert status.completed == 1
    assert status.successful == 0
    assert status.failed == 1
    assert status.successful_docs == []
    assert status.failed_docs == ["/some/uri-1.xml"]

    status.add_failed_doc("/some/uri-2.xml")
    assert status.completed == 2
    assert status.successful == 0
    assert status.failed == 2
    assert status.successful_docs == []
    assert status.failed_docs == ["/some/uri-1.xml", "/some/uri-2.xml"]


def test_add_failed_docs():
    status = DocumentJobStatus()
    assert status.completed == 0
    assert status.successful == 0
    assert status.failed == 0
    assert status.successful_docs == []
    assert status.failed_docs == []

    status.add_failed_docs(["/some/uri-1.xml"])
    assert status.completed == 1
    assert status.successful == 0
    assert status.failed == 1
    assert status.successful_docs == []
    assert status.failed_docs == ["/some/uri-1.xml"]

    status.add_failed_docs(["/some/uri-2.xml", "/some/uri-3.xml"])
    assert status.completed == 3
    assert status.successful == 0
    assert status.failed == 3
    assert status.successful_docs == []
    assert status.failed_docs == [
        "/some/uri-1.xml",
        "/some/uri-2.xml",
        "/some/uri-3.xml",
    ]
