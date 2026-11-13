from __future__ import annotations

import zlib
from uuid import uuid4
from xml.etree.ElementTree import ElementTree, fromstring

import pytest

from mlclient import MLClient
from mlclient.calls import ApiCall
from mlclient.jobs import WriteDocumentsJob
from mlclient.models import (
    BinaryDocument,
    JSONDocument,
    Metadata,
    MetadataDocument,
    TextDocument,
    XMLDocument,
)
from tests.utils import documents_client as docs_client_utils
from tests.utils.resources import render_test_resource


class TransformCall(ApiCall):
    """Install or remove a uniquely named content transform."""

    def __init__(self, name: str, method: str, body: str | None = None):
        super().__init__(method=method, body=body, content_type="application/xquery")
        self._name = name

    @property
    def endpoint(self):
        return f"/v1/config/transforms/{self._name}"


@pytest.fixture(scope="module")
def tag_transform():
    name = f"mlclient-documents-{uuid4().hex}"
    body = render_test_resource(__file__, "tag-transform.xqy", name=name)
    with MLClient() as ml:
        ml.rest.call(TransformCall(name, "PUT", body)).raise_for_status()
        try:
            yield name
        finally:
            ml.rest.call(TransformCall(name, "DELETE")).raise_for_status()


def test_create_read_and_remove_xml_document():
    uri = "/some/dir/doc1.xml"
    content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    doc = XMLDocument(content, uri)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_data({uri: doc})
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_json_document():
    uri = "/some/dir/doc2.json"
    content = b'{"root": {"child": "data"}}'
    doc = JSONDocument(content, uri)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_data({uri: doc})
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_text_document():
    uri = "/some/dir/doc3.xqy"
    content = b'xquery version "1.0-ml";\n\nfn:current-date()'
    doc = TextDocument(content, uri)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_data({uri: doc})
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_binary_document():
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc = BinaryDocument(content, uri)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_data({uri: doc})
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_document_with_metadata():
    uri = "/some/dir/doc2.json"
    content = {"root": {"child": "data"}}
    metadata = Metadata(collections=["test-collection"])
    doc = JSONDocument(content, uri, metadata)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_content_with_metadata(
            {uri: doc},
        )
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_document_with_raw_metadata():
    uri = "/some/dir/doc2.json"
    content = b'{"root":{"child":"data"}}'
    metadata = b'{"collections": ["test-collection"]}'
    doc = JSONDocument(content, uri, metadata)
    expected = JSONDocument(
        content,
        uri,
        Metadata(collections=["test-collection"]),
    )

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_content_with_metadata(
            {uri: expected},
        )
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_multiple_documents():
    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    doc_1 = XMLDocument(doc_1_content, doc_1_uri)

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = b'{"root": {"child": "data"}}'
    doc_2 = JSONDocument(doc_2_content, doc_2_uri)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = b'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3 = TextDocument(doc_3_content, doc_3_uri)

    doc_4_uri = "/some/dir/doc4.zip"
    doc_4_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc_4 = BinaryDocument(doc_4_content, doc_4_uri)

    try:
        docs_client_utils.assert_documents_do_not_exist(
            [doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri],
        )
        docs_client_utils.write_documents([doc_1, doc_2, doc_3, doc_4])
        docs_client_utils.assert_documents_exist_and_confirm_data(
            {
                doc_1_uri: doc_1,
                doc_2_uri: doc_2,
                doc_3_uri: doc_3,
                doc_4_uri: doc_4,
            },
        )
    finally:
        docs_client_utils.delete_documents([doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri])
        docs_client_utils.assert_documents_do_not_exist(
            [doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri],
        )


def test_create_read_and_remove_multiple_documents_with_default_and_custom_metadata():
    default_metadata_1 = Metadata(collections=["default-collection-1"])
    default_metadata_2 = Metadata(collections=["default-collection-2"])

    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content = ElementTree(fromstring("<root><parent>data</parent></root>"))
    doc_1 = XMLDocument(doc_1_content, doc_1_uri)
    doc_1_expected = XMLDocument(doc_1_content, doc_1_uri, Metadata())

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = {"root": {"child": "data"}}
    doc_2 = JSONDocument(doc_2_content, doc_2_uri)
    doc_2_expected = JSONDocument(doc_2_content, doc_2_uri, default_metadata_1)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = 'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3_metadata = Metadata(collections=["doc-3-collection"])
    doc_3 = TextDocument(doc_3_content, doc_3_uri, doc_3_metadata)
    doc_3_expected = doc_3

    doc_4_uri = "/some/dir/doc4.zip"
    doc_4_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc_4 = BinaryDocument(doc_4_content, doc_4_uri)
    doc_4_expected = BinaryDocument(doc_4_content, doc_4_uri, default_metadata_1)

    doc_5_uri = "/some/dir/doc5.json"
    doc_5_content = {"root": {"child": "data"}}
    doc_5_metadata = Metadata(collections=["doc-5-collection"])
    doc_5 = JSONDocument(doc_5_content, doc_5_uri, doc_5_metadata)
    doc_5_expected = doc_5

    doc_6_uri = "/some/dir/doc6.json"
    doc_6_content = {"root": {"child": "data"}}
    doc_6 = JSONDocument(doc_6_content, doc_6_uri)
    doc_6_expected = JSONDocument(doc_6_content, doc_6_uri, default_metadata_2)

    try:
        docs_client_utils.assert_documents_do_not_exist(
            [doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri, doc_5_uri, doc_6_uri],
        )
        docs_client_utils.write_documents(
            [
                doc_1,
                default_metadata_1,
                doc_2,
                doc_3,
                doc_4,
                default_metadata_2,
                doc_5,
                doc_6,
            ],
        )
        docs_client_utils.assert_documents_exist_and_confirm_content_with_metadata(
            {
                doc_1_uri: doc_1_expected,
                doc_2_uri: doc_2_expected,
                doc_3_uri: doc_3_expected,
                doc_4_uri: doc_4_expected,
                doc_5_uri: doc_5_expected,
                doc_6_uri: doc_6_expected,
            },
        )
    finally:
        docs_client_utils.delete_documents(
            [doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri, doc_5_uri, doc_6_uri],
        )
        docs_client_utils.assert_documents_do_not_exist(
            [doc_1_uri, doc_2_uri, doc_3_uri, doc_4_uri, doc_5_uri, doc_6_uri],
        )


def test_update_document():
    uri = "/some/dir/doc1.xml"
    content_1 = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data1</child></root>'
    )
    content_2 = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data2</child></root>'
    )
    doc_1 = XMLDocument(content_1, uri)
    doc_2 = XMLDocument(content_2, uri)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc_1)
        docs_client_utils.assert_documents_exist_and_confirm_data({uri: doc_1})
        docs_client_utils.write_documents(doc_2)
        docs_client_utils.assert_documents_exist_and_confirm_data({uri: doc_2})
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_update_document_metadata():
    uri = "/some/dir/doc2.json"
    content = {"root": {"child": "data"}}
    metadata_1 = Metadata()
    metadata_2 = Metadata(collections=["test-metadata"])
    metadata_1_doc = MetadataDocument(uri, metadata_1)
    metadata_2_doc = MetadataDocument(uri, metadata_2)
    doc = JSONDocument(content, uri, metadata_1)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_data(
            {uri: metadata_1_doc},
            category=["metadata"],
        )
        docs_client_utils.write_documents(metadata_2_doc)
        docs_client_utils.assert_documents_exist_and_confirm_data(
            {uri: metadata_2_doc},
            category=["metadata"],
        )
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_read_and_delete_exceed_httpx_url_length_limit():
    """Verify DocumentsService auto-batches URIs past the httpx URL limit.

    With the URI template "/some/dir/doc-{N}.xml" the httpx MAX_URL_LENGTH
    (65536 bytes) is exceeded around 2020 URIs in a single request. This test
    uses 2050 URIs to prove the service transparently splits the request into
    multiple batches end-to-end (write via job, then read, read_stream, delete
    via the service) without raising httpx.InvalidURL.
    """
    uris_count = 2050
    docs = list(docs_client_utils.generate_docs(count=uris_count))
    uris = [doc.uri for doc in docs]

    try:
        docs_client_utils.assert_documents_do_not_exist(uris)

        write_job = WriteDocumentsJob()
        write_job.with_documents_input(docs)
        write_job.run_sync()
        assert write_job.report.successful == uris_count

        with MLClient() as ml:
            read_docs = ml.documents.read(uris)
            assert len(read_docs) == uris_count
            for uri in uris:
                assert uri in read_docs

            streamed_uris = {doc.uri for doc in ml.documents.read_stream(uris)}
            assert streamed_uris == set(uris)

            ml.documents.delete(uris)

        docs_client_utils.assert_documents_do_not_exist(uris)
    finally:
        docs_client_utils.delete_documents(uris)


def test_write_within_transaction_is_isolated_until_commit():
    uri = "/some/dir/txn-doc.xml"
    doc = XMLDocument(b"<root><child>data</child></root>", uri)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        with MLClient() as ml:
            txid = _open_transaction(ml)
            ml.documents.write(doc, txid=txid)
            docs_client_utils.assert_document_does_not_exist(uri)
            ml.rest.transactions.post(txid, result="commit")
        docs_client_utils.assert_documents_exist_and_confirm_data({uri: doc})
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_write_within_transaction_rolled_back_is_discarded():
    uri = "/some/dir/txn-doc.xml"
    doc = XMLDocument(b"<root><child>data</child></root>", uri)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        with MLClient() as ml:
            txid = _open_transaction(ml)
            ml.documents.write(doc, txid=txid)
            ml.rest.transactions.post(txid, result="rollback")
        docs_client_utils.assert_document_does_not_exist(uri)
    finally:
        docs_client_utils.delete_documents(uri)


def test_read_single_document_with_transform(tag_transform):
    uri = "/some/dir/transform-read.xml"

    try:
        docs_client_utils.write_documents(XMLDocument(b"<root>data</root>", uri))
        with MLClient() as ml:
            doc = ml.documents.read(
                uri,
                transform=tag_transform,
                transform_params={"value": "read"},
            )
        assert doc.content.getroot().attrib == {"transformed": "read"}
    finally:
        docs_client_utils.delete_documents(uri)


def test_read_multiple_documents_with_transform(tag_transform):
    uris = ["/some/dir/transform-read-1.xml", "/some/dir/transform-read-2.xml"]

    try:
        docs_client_utils.write_documents(
            [XMLDocument(b"<root>data</root>", uri) for uri in uris],
        )
        with MLClient() as ml:
            docs = ml.documents.read(
                uris,
                transform=tag_transform,
                transform_params={"value": "read"},
            )
        assert {uri: doc.content.getroot().attrib for uri, doc in docs.items()} == {
            uri: {"transformed": "read"} for uri in uris
        }
    finally:
        docs_client_utils.delete_documents(uris)


def test_write_with_transform_stores_transformed_content(tag_transform):
    uri = "/some/dir/transform-write.xml"

    try:
        with MLClient() as ml:
            ml.documents.write(
                XMLDocument(b"<root>data</root>", uri),
                transform=tag_transform,
                transform_params={"value": "write"},
            )
            doc = ml.documents.read(uri)
        assert doc.content.getroot().attrib == {"transformed": "write"}
    finally:
        docs_client_utils.delete_documents(uri)


def test_read_multiple_documents_at_earlier_timestamp():
    uris = ["/some/dir/snapshot-1.xml", "/some/dir/snapshot-2.xml"]

    try:
        docs_client_utils.write_documents(
            [XMLDocument(b"<root>old</root>", uri) for uri in uris],
        )
        with MLClient() as ml:
            response = ml.rest.documents.get(uris[0])
            timestamp = response.headers["ML-Effective-Timestamp"]
            ml.documents.write([XMLDocument(b"<root>new</root>", uri) for uri in uris])

            snapshot = ml.documents.read(uris, timestamp=timestamp)
            current = ml.documents.read(uris)

        assert {
            uri: doc.content.getroot().text for uri, doc in snapshot.items()
        } == dict.fromkeys(uris, "old")
        assert {
            uri: doc.content.getroot().text for uri, doc in current.items()
        } == dict.fromkeys(uris, "new")
    finally:
        docs_client_utils.delete_documents(uris)


def _open_transaction(ml: MLClient) -> str:
    location = ml.rest.transactions.create().headers["Location"]
    return location.rsplit("/", 1)[-1]
