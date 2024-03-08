from __future__ import annotations

import zlib
from xml.etree.ElementTree import ElementTree, fromstring

from mlclient.structures import (
    BinaryDocument,
    DocumentType,
    JSONDocument,
    Metadata,
    MetadataDocument,
    RawDocument,
    RawStringDocument,
    TextDocument,
    XMLDocument,
)
from tests.utils import documents_client as docs_client_utils


def test_create_read_and_remove_xml_document():
    uri = "/some/dir/doc1.xml"
    content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    doc = RawDocument(content, uri, DocumentType.XML)

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
    doc = RawDocument(content, uri, DocumentType.JSON)

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
    doc = RawDocument(content, uri, DocumentType.TEXT)

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
    doc = RawDocument(content, uri, DocumentType.BINARY)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_data({uri: doc})
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_document_using_string_output_type():
    uri = "/some/dir/doc1.xml"
    content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>\n'
    )
    doc = RawDocument(content, uri, DocumentType.XML)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_data(
            {uri: doc},
            output_type=str,
        )
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_document_using_bytes_output_type():
    uri = "/some/dir/doc1.xml"
    content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>\n'
    )
    doc = RawDocument(content, uri, DocumentType.XML)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_data(
            {uri: doc},
            output_type=bytes,
        )
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


def test_create_read_and_remove_document_with_metadata_using_string_output_type():
    uri = "/some/dir/doc2.json"
    content = '{"root":{"child":"data"}}'
    metadata = (
        "{"
        '"collections":["test-collection"],'
        '"permissions":[],'
        '"properties":{},'
        '"quality":0,'
        '"metadataValues":{}'
        "}"
    )
    doc = RawStringDocument(content, uri, DocumentType.JSON, metadata)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_content_with_metadata(
            {uri: doc},
            output_type=str,
        )
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


def test_create_read_and_remove_document_with_metadata_using_bytes_output_type():
    uri = "/some/dir/doc2.json"
    content = b'{"root":{"child":"data"}}'
    metadata = (
        b"{"
        b'"collections":["test-collection"],'
        b'"permissions":[],'
        b'"properties":{},'
        b'"quality":0,'
        b'"metadataValues":{}'
        b"}"
    )
    doc = RawDocument(content, uri, DocumentType.JSON, metadata)

    try:
        docs_client_utils.assert_document_does_not_exist(uri)
        docs_client_utils.write_documents(doc)
        docs_client_utils.assert_documents_exist_and_confirm_content_with_metadata(
            {uri: doc},
            output_type=bytes,
        )
    finally:
        docs_client_utils.delete_documents(uri)
        docs_client_utils.assert_document_does_not_exist(uri)


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


def test_create_read_and_remove_multiple_documents_using_string_output_type():
    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    doc_1 = RawDocument(doc_1_content, doc_1_uri, DocumentType.XML)

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = b'{"root":{"child":"data"}}'
    doc_2 = RawDocument(doc_2_content, doc_2_uri, DocumentType.JSON)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = b'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3 = RawDocument(doc_3_content, doc_3_uri, DocumentType.TEXT)

    try:
        docs_client_utils.assert_documents_do_not_exist(
            [doc_1_uri, doc_2_uri, doc_3_uri],
        )
        docs_client_utils.write_documents([doc_1, doc_2, doc_3])
        docs_client_utils.assert_documents_exist_and_confirm_data(
            {
                doc_1_uri: doc_1,
                doc_2_uri: doc_2,
                doc_3_uri: doc_3,
            },
            output_type=str,
        )
    finally:
        docs_client_utils.delete_documents([doc_1_uri, doc_2_uri, doc_3_uri])
        docs_client_utils.assert_documents_do_not_exist(
            [doc_1_uri, doc_2_uri, doc_3_uri],
        )


def test_create_read_and_remove_multiple_documents_using_bytes_output_type():
    doc_1_uri = "/some/dir/doc1.xml"
    doc_1_content = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    doc_1 = RawDocument(doc_1_content, doc_1_uri, DocumentType.XML)

    doc_2_uri = "/some/dir/doc2.json"
    doc_2_content = b'{"root":{"child":"data"}}'
    doc_2 = RawDocument(doc_2_content, doc_2_uri, DocumentType.JSON)

    doc_3_uri = "/some/dir/doc3.xqy"
    doc_3_content = b'xquery version "1.0-ml";\n\nfn:current-date()'
    doc_3 = RawDocument(doc_3_content, doc_3_uri, DocumentType.TEXT)

    doc_4_uri = "/some/dir/doc4.zip"
    doc_4_content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')
    doc_4 = RawDocument(doc_4_content, doc_4_uri, DocumentType.BINARY)

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
            output_type=bytes,
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
    doc_1 = RawDocument(content_1, uri, DocumentType.XML)
    doc_2 = RawDocument(content_2, uri, DocumentType.XML)

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
