import pytest

from mlclient.clients import DocumentsClient
from mlclient.exceptions import MarkLogicError
from mlclient.model import DocumentType, Document, RawDocument


def test_manage_xml_document():
    uri = "/some/dir/doc1.xml"
    content = b"<root><child>data</child></root>"
    doc = RawDocument(content, uri, DocumentType.XML)

    _assert_document_does_not_exist(uri)
    try:
        _create_document(doc)
        _assert_document_exists_and_confirm_content(doc)
    finally:
        _delete_document(uri)
        _assert_document_does_not_exist(uri)


def _assert_document_does_not_exist(
    uri: str,
):
    expected_msg = (
        "[500 Internal Server Error] (RESTAPI-NODOCUMENT) "
        "RESTAPI-NODOCUMENT: (err:FOER0000) "
        "Resource or document does not exist:  "
        f"category: content message: {uri}"
    )
    with DocumentsClient(auth_method="digest") as docs_client, pytest.raises(
        MarkLogicError,
    ) as err:
        docs_client.read(uri)
    assert err.value.args[0] == expected_msg


def _assert_document_exists_and_confirm_content(
    expected_doc: Document,
):
    with DocumentsClient(auth_method="digest") as docs_client:
        actual_doc = docs_client.read(expected_doc.uri)
        assert actual_doc.uri == expected_doc.uri
        assert actual_doc.doc_type == expected_doc.doc_type
        assert expected_doc.content_bytes in actual_doc.content_bytes
        assert actual_doc.metadata == expected_doc.metadata
        assert actual_doc.temporal_collection == expected_doc.temporal_collection


def _create_document(
    doc: Document,
):
    with DocumentsClient(auth_method="digest") as docs_client:
        resp = docs_client.create(doc)
        documents = resp["documents"]
        assert len(documents) == 1
        assert documents[0]["uri"] == doc.uri
        assert documents[0]["mime-type"] == "application/xml"


def _delete_document(
    uri: str,
):
    try:
        with DocumentsClient(auth_method="digest") as docs_client:
            docs_client.delete(uri)
    except MarkLogicError as err:
        pytest.fail(str(err))
