from __future__ import annotations

import zlib

import pytest

from mlclient.clients import DocumentsClient
from mlclient.exceptions import MarkLogicError
from mlclient.mimetypes import Mimetypes
from mlclient.model import (
    Document,
    DocumentType,
    JSONDocument,
    Metadata,
    MetadataDocument,
    RawDocument,
)


def test_create_read_and_remove_xml_document():
    uri = "/some/dir/doc1.xml"
    content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    doc = RawDocument(content, uri, DocumentType.XML)

    _assert_document_does_not_exist(uri)
    try:
        _write_documents(doc)
        _assert_document_exists_and_confirm_data(uri, doc)
    finally:
        _delete_documents(uri)
        _assert_document_does_not_exist(uri)


def test_create_read_and_remove_json_document():
    uri = "/some/dir/doc2.json"
    content = b'{"root": {"child": "data"}}'
    doc = RawDocument(content, uri, DocumentType.JSON)

    _assert_document_does_not_exist(uri)
    try:
        _write_documents(doc)
        _assert_document_exists_and_confirm_data(uri, doc)
    finally:
        _delete_documents(uri)
        _assert_document_does_not_exist(uri)


def test_create_read_and_remove_text_document():
    uri = "/some/dir/doc3.xqy"
    content = b'xquery version "1.0-ml";\n\nfn:current-date()'
    doc = RawDocument(content, uri, DocumentType.TEXT)

    _assert_document_does_not_exist(uri)
    try:
        _write_documents(doc)
        _assert_document_exists_and_confirm_data(uri, doc)
    finally:
        _delete_documents(uri)
        _assert_document_does_not_exist(uri)


def test_create_read_and_remove_binary_document():
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc = RawDocument(content, uri, DocumentType.BINARY)

    _assert_document_does_not_exist(uri)
    try:
        _write_documents(doc)
        _assert_document_exists_and_confirm_data(uri, doc)
    finally:
        _delete_documents(uri)
        _assert_document_does_not_exist(uri)


def test_create_read_and_remove_document_with_metadata():
    uri = "/some/dir/doc2.json"
    content = {"root": {"child": "data"}}
    metadata = Metadata(collections=["test-collection"])
    doc = JSONDocument(content, uri, metadata)

    _assert_document_does_not_exist(uri)
    try:
        _write_documents(doc)
        _assert_document_exists_and_confirm_content_with_metadata(uri, doc)
    finally:
        _delete_documents(uri)
        _assert_document_does_not_exist(uri)


def test_create_read_and_remove_multiple_documents():
    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    doc_1 = RawDocument(doc_1_content, doc_1_uri, DocumentType.XML)

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = b'{"root": {"child": "data"}}'
    doc_2 = RawDocument(doc_2_content, doc_2_uri, DocumentType.JSON)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = b'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3 = RawDocument(doc_3_content, doc_3_uri, DocumentType.TEXT)

    doc_4_uri = "/some/dir/doc4.zip"
    doc_4_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc_4 = RawDocument(doc_4_content, doc_4_uri, DocumentType.BINARY)

    _assert_documents_do_not_exist([doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri])
    try:
        _write_documents([doc_1, doc_2, doc_3, doc_4])
        _assert_document_exists_and_confirm_data(doc_1_uri, doc_1)
        _assert_document_exists_and_confirm_data(doc_2_uri, doc_2)
        _assert_document_exists_and_confirm_data(doc_3_uri, doc_3)
        _assert_document_exists_and_confirm_data(doc_4_uri, doc_4)
    finally:
        _delete_documents([doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri])
        _assert_documents_do_not_exist([doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri])


def test_update_document():
    uri = "/some/dir/doc1.xml"
    content_1 = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data1</child></root>'
    )
    content_2 = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data2</child></root>'
    )
    doc_1 = RawDocument(content_1, uri, DocumentType.XML)
    doc_2 = RawDocument(content_2, uri, DocumentType.XML)

    _assert_document_does_not_exist(uri)
    try:
        _write_documents(doc_1)
        _assert_document_exists_and_confirm_data(uri, doc_1)
        _write_documents(doc_2)
        _assert_document_exists_and_confirm_data(uri, doc_2)
    finally:
        _delete_documents(uri)
        _assert_document_does_not_exist(uri)


def test_update_document_metadata():
    uri = "/some/dir/doc2.json"
    content = {"root": {"child": "data"}}
    metadata = Metadata(collections=["test-metadata"])
    doc_1 = JSONDocument(content, uri, Metadata())
    doc_2 = JSONDocument(content, uri, metadata)
    metadata_doc = MetadataDocument(uri, metadata)

    _assert_document_does_not_exist(uri)
    try:
        _write_documents(doc_1)
        _assert_document_exists_and_confirm_content_with_metadata(uri, doc_1)
        _write_documents(metadata_doc)
        _assert_document_exists_and_confirm_content_with_metadata(uri, doc_2)
    finally:
        _delete_documents(uri)
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


def _assert_documents_do_not_exist(
    uris: list,
):
    with DocumentsClient(auth_method="digest") as docs_client:
        assert docs_client.read(uris) == []


def _assert_document_exists_and_confirm_content_with_metadata(
    uri: str,
    expected_doc: Document,
):
    _assert_document_exists_and_confirm_data(uri, expected_doc, ["content", "metadata"])


def _assert_document_exists_and_confirm_data(
    uri: str,
    expected_doc: Document,
    category: str | list[str] = "content",
):
    with DocumentsClient(auth_method="digest") as docs_client:
        actual_doc = docs_client.read(uri, category)
        assert actual_doc.uri == expected_doc.uri
        assert actual_doc.doc_type == expected_doc.doc_type
        assert actual_doc.content_bytes == expected_doc.content_bytes
        if category not in ("content", ["content"]):
            assert actual_doc.metadata == expected_doc.metadata


def _write_documents(
    docs: Document | Metadata | list[Document | Metadata],
):
    if not isinstance(docs, list):
        docs = [docs]
    with DocumentsClient(auth_method="digest") as docs_client:
        resp = docs_client.create(docs)
        documents = resp["documents"]
        assert len(documents) == len(docs)
        for doc in docs:
            response_doc = next((d for d in documents if d["uri"] == doc.uri), None)
            assert response_doc is not None
            assert response_doc["uri"] == doc.uri
            if "content" in response_doc["category"]:
                assert response_doc["mime-type"] == Mimetypes.get_mimetype(doc.uri)
            else:
                assert response_doc["mime-type"] == ""


def _delete_documents(
    uri: str | list[str],
):
    try:
        with DocumentsClient(auth_method="digest") as docs_client:
            docs_client.delete(uri)
    except MarkLogicError as err:
        pytest.fail(str(err))
