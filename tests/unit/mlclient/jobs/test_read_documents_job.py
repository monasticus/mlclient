from __future__ import annotations

import json
import xml.etree.ElementTree as ElemTree
from typing import Iterable

import pytest
import responses

from mlclient.jobs import ReadDocumentsJob
from mlclient.structures import Document, DocumentType, XMLDocument
from mlclient.structures.calls import DocumentsBodyPart
from tests.utils import MLResponseBuilder


@responses.activate
def test_basic_job_with_uris_input():
    uris_count = 5
    uris = [f"/some/dir/doc{i+1}.xml" for i in range(uris_count)]

    _setup_responses(uris)

    job = ReadDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.start()
    docs = job.get_documents()

    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == uris_count
    assert job.status.successful == uris_count
    assert job.status.failed == 0
    _confirm_documents_data(uris, docs)


@responses.activate
def test_basic_job_with_multiple_inputs():
    uris_count = 500
    uris = [f"/some/dir/doc{i+1}.xml" for i in range(uris_count)]

    _setup_responses(uris)

    job = ReadDocumentsJob(thread_count=1, batch_size=500)
    assert job.thread_count == 1
    assert job.batch_size == 500
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris[:250])
    job.with_uris_input(uris[250:])
    job.start()
    docs = job.get_documents()

    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == uris_count
    assert job.status.successful == uris_count
    assert job.status.failed == 0
    _confirm_documents_data(uris, docs)


@responses.activate
def test_job_with_custom_database():
    uris_count = 5
    uris = [f"/some/dir/doc{i+1}.xml" for i in range(uris_count)]

    _setup_responses(uris, database="Documents")

    job = ReadDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_database("Documents")
    job.with_uris_input(uris)
    job.start()
    docs = job.get_documents()

    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == uris_count
    assert job.status.successful == uris_count
    assert job.status.failed == 0
    _confirm_documents_data(uris, docs)


@responses.activate
def test_job_with_full_metadata():
    uris_count = 5
    uris = [f"/some/dir/doc{i+1}.xml" for i in range(uris_count)]

    _setup_responses(uris, metadata=["metadata"])

    job = ReadDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.with_metadata()
    job.start()
    docs = job.get_documents()

    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == uris_count
    assert job.status.successful == uris_count
    assert job.status.failed == 0
    _confirm_documents_data(uris, docs, metadata=["metadata"])


@responses.activate
def test_job_with_some_metadata_categories():
    uris_count = 5
    uris = [f"/some/dir/doc{i+1}.xml" for i in range(uris_count)]

    _setup_responses(uris, metadata=["quality"])

    job = ReadDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.with_metadata("quality")
    job.start()
    docs = job.get_documents()

    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == uris_count
    assert job.status.successful == uris_count
    assert job.status.failed == 0
    _confirm_documents_data(uris, docs, metadata=["quality"])


@pytest.mark.asyncio()
async def test_multi_thread_job():
    @responses.activate
    async def run():
        uris_count = 150
        document_body_parts = list(_get_test_document_body_parts(uris_count))

        builder = MLResponseBuilder()
        builder.with_base_url("http://localhost:8002/v1/documents")
        builder.build_with_docs_callback(document_body_parts)

        uris = [f"/some/dir/doc{i+1}.xml" for i in range(uris_count)]
        job = ReadDocumentsJob(batch_size=5)
        assert job.thread_count > 1
        assert job.batch_size == 5
        job.with_client_config(auth_method="digest")
        job.with_uris_input(uris)
        job.start()
        docs = job.get_documents()

        if len(docs) != uris_count:
            return False

        calls = responses.calls
        assert len(calls) >= 30
        assert job.status.completed == uris_count
        assert job.status.successful == uris_count
        assert job.status.failed == 0
        _confirm_documents_data(uris, docs)
        return True

    all_docs_processed = False
    while not all_docs_processed:
        all_docs_processed = await run()


@responses.activate
def test_failing_job():
    uris_count = 5
    uris = [f"/some/dir/doc{i+1}.xml" for i in range(uris_count)]

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    for uri in uris:
        builder.with_request_param("uri", uri)
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_status(401)
    builder.with_response_body(
        {
            "errorResponse": {
                "statusCode": 401,
                "status": "Unauthorized",
                "message": "401 Unauthorized",
            },
        },
    )
    builder.build_get()

    job = ReadDocumentsJob(thread_count=1, batch_size=5)
    assert job.thread_count == 1
    assert job.batch_size == 5
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.start()
    docs = job.get_documents()

    calls = responses.calls
    assert len(calls) == 1
    assert job.status.completed == uris_count
    assert job.status.successful == 0
    assert job.status.failed == uris_count
    assert len(docs) == 0


def _setup_responses(
    uris: list[str],
    metadata: list[str] | None = None,
    **kwargs,
):
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    for uri in uris:
        builder.with_request_param("uri", uri)
    for param_name, param_value in kwargs.items():
        builder.with_request_param(param_name, param_value)
    if metadata:
        builder.with_request_param("category", "content")
        for category in metadata:
            builder.with_request_param("category", category)
    builder.with_request_param("format", "json")
    builder.with_response_body_multipart_mixed()
    builder.with_response_status(200)
    for document_body_part in _get_test_document_body_parts(len(uris), metadata):
        builder.with_response_documents_body_part(document_body_part)
    builder.build_get()


def _get_test_document_body_parts(
    count: int,
    metadata: list[str] | None = None,
) -> Iterable[DocumentsBodyPart]:
    for i in range(count):
        yield DocumentsBodyPart(
            **{
                "content-type": "application/xml",
                "content-disposition": "attachment; "
                f'filename="/some/dir/doc{i+1}.xml"; '
                "category=content; "
                "format=xml",
                "content": '<?xml version="1.0" encoding="UTF-8"?>\n'
                f"<root><child>data{i+1}</child></root>",
            },
        )
        if metadata:
            categories = "; ".join([f"category={c}" for c in metadata])
            content = {}
            if "metadata" in metadata or "collections" in metadata:
                content["collections"] = ["test-collection"]
            if "metadata" in metadata or "quality" in metadata:
                content["quality"] = 5
            if "metadata" in metadata or "permissions" in metadata:
                content["permissions"] = []
            if "metadata" in metadata or "properties" in metadata:
                content["properties"] = {}
            if "metadata" in metadata or "metadataValues" in metadata:
                content["metadataValues"] = {}
            yield DocumentsBodyPart(
                **{
                    "content-type": "application/json",
                    "content-disposition": "attachment; "
                    f'filename="/some/dir/doc{i+1}.xml"; '
                    f"{categories}; "
                    "format=json",
                    "content": json.dumps(content),
                },
            )


def _confirm_documents_data(
    uris: list[str],
    docs: list[Document],
    metadata: list[str] | None = None,
):
    for i, uri in enumerate(uris):
        doc = next(doc for doc in docs if doc.uri == uri)
        assert isinstance(doc, XMLDocument)
        assert doc.uri == uri
        assert doc.doc_type == DocumentType.XML
        if metadata:
            if "metadata" in metadata:
                metadata = [
                    "quality",
                    "collections",
                    "permissions",
                    "properties",
                    "metadata_values",
                ]
            assert "quality" not in metadata or doc.metadata.quality() == 5
            assert "collections" not in metadata or doc.metadata.collections() == [
                "test-collection",
            ]
            assert "permissions" not in metadata or doc.metadata.permissions() == []
            assert "properties" not in metadata or doc.metadata.properties() == {}
            assert (
                "metadata_values" not in metadata
                or doc.metadata.metadata_values() == {}
            )
        else:
            assert doc.metadata is None
        assert doc.temporal_collection is None
        assert isinstance(doc.content, ElemTree.ElementTree)
        assert doc.content.getroot().tag == "root"
        assert doc.content.getroot().attrib == {}
        children = list(doc.content.getroot())
        assert len(children) == 1
        assert children[0].tag == "child"
        assert children[0].text == f"data{i+1}"
        assert children[0].attrib == {}
