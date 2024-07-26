from __future__ import annotations

import pytest
from mimeo import MimeoConfig, MimeoConfigFactory, Mimeograph

from mlclient.clients import DocumentsClient
from mlclient.exceptions import MarkLogicError
from mlclient.mimetypes import Mimetypes
from mlclient.structures import Document, DocumentType, Metadata, RawDocument


def assert_document_does_not_exist(
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


def assert_documents_exist(
    uris: list,
):
    with DocumentsClient(auth_method="digest") as docs_client:
        assert docs_client.read(uris, output_type=bytes) != []


def assert_documents_do_not_exist(
    uris: list,
):
    with DocumentsClient(auth_method="digest") as docs_client:
        assert docs_client.read(uris, output_type=bytes) == []


def assert_documents_exist_and_confirm_content_with_metadata(
    expected: dict,
    output_type: type | None = None,
):
    assert_documents_exist_and_confirm_data(
        expected,
        ["content", "metadata"],
        output_type,
    )


def assert_documents_exist_and_confirm_data(
    expected: dict,
    category: str | list[str] = "content",
    output_type: type | None = None,
):
    with DocumentsClient(auth_method="digest") as docs_client:
        actual_docs = docs_client.read(
            list(expected.keys()),
            category,
            output_type=output_type,
        )
        for actual_doc in actual_docs:
            expected_doc = next(
                (doc for uri, doc in expected.items() if uri == actual_doc.uri),
                None,
            )
            assert expected_doc is not None
            assert actual_doc.uri == expected_doc.uri
            assert actual_doc.doc_type == expected_doc.doc_type
            if output_type is str:
                assert actual_doc.content == expected_doc.content_string
            elif output_type is bytes:
                assert actual_doc.content == expected_doc.content_bytes
            else:
                assert actual_doc.content_bytes == expected_doc.content_bytes
            if category not in ("content", ["content"]):
                assert actual_doc.metadata == expected_doc.metadata


def write_documents(
    docs: Document | Metadata | list[Document | Metadata],
):
    with DocumentsClient(auth_method="digest") as docs_client:
        resp = docs_client.create(docs)
        documents = resp["documents"]
        if not isinstance(docs, list):
            docs = [docs]
        expected_docs = [doc for doc in docs if type(doc) is not Metadata]
        assert len(documents) == len(expected_docs)
        for doc in expected_docs:
            response_doc = next((d for d in documents if d["uri"] == doc.uri), None)
            assert response_doc is not None
            assert response_doc["uri"] == doc.uri
            if "content" in response_doc["category"]:
                assert response_doc["mime-type"] == Mimetypes.get_mimetype(doc.uri)
            else:
                assert response_doc["mime-type"] == ""


def delete_documents(
    uri: str | list[str],
):
    try:
        with DocumentsClient(auth_method="digest") as docs_client:
            docs_client.delete(uri)
    except MarkLogicError as err:
        pytest.fail(str(err))


def generate_docs(
    count: int = 100,
    content: bytes | None = None,
    document_type: DocumentType = DocumentType.XML,
    uri_template: str = "/some/dir/doc-{}.xml",
    with_metadata: bool = False,
):
    content = (
        content
        or b'<?xml version="1.0" encoding="UTF-8"?>\n<root><child>data</child></root>'
    )
    metadata = None
    if with_metadata:
        metadata = (
            Metadata(
                collections=["test-collection"],
                quality=5,
            )
            .to_json_string()
            .encode("utf-8")
        )
    for i in range(count):
        yield RawDocument(
            content=content,
            metadata=metadata,
            uri=uri_template.format(i + 1),
            doc_type=document_type,
        )


def generate_docs_with_mimeo(
    docs_configs: list[tuple[str, str, int]],
):
    mimeo_configs = (_get_mimeo_config(*docs_config) for docs_config in docs_configs)

    with Mimeograph() as mimeo:
        for mimeo_config in mimeo_configs:
            config_id = f"config-{mimeo_config.templates[0].count}"
            mimeo.submit((config_id, mimeo_config))


def _get_mimeo_config(
    mimeo_config_path: str,
    output_path: str,
    count: int = -1,
) -> MimeoConfig:
    mimeo_config = MimeoConfigFactory.parse(mimeo_config_path)
    mimeo_config.output.directory_path = output_path
    if count > 0:
        mimeo_config.templates[0].count = count
    return mimeo_config
