from __future__ import annotations

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
    _confirm_documents_content(uris, docs)


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
    _confirm_documents_content(uris, docs)


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
    _confirm_documents_content(uris, docs)


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
        _confirm_documents_content(uris, docs)
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


def _setup_responses(uris: list[str], **kwargs):
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    for uri in uris:
        builder.with_request_param("uri", uri)
    for param_name, param_value in kwargs.items():
        builder.with_request_param(param_name, param_value)
    builder.with_request_param("format", "json")
    builder.with_response_body_multipart_mixed()
    builder.with_response_status(200)
    for document_body_part in _get_test_document_body_parts(len(uris)):
        builder.with_response_documents_body_part(document_body_part)
    builder.build_get()


def _get_test_document_body_parts(
    count: int,
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


def _confirm_documents_content(uris: list[str], docs: list[Document]):
    for i, uri in enumerate(uris):
        doc = next(doc for doc in docs if doc.uri == uri)
        assert isinstance(doc, XMLDocument)
        assert doc.uri == uri
        assert doc.doc_type == DocumentType.XML
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
