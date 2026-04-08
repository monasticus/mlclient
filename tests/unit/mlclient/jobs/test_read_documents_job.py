from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ElemTree
from collections.abc import Iterable
from pathlib import Path

import respx

from mlclient.exceptions import MarkLogicError
from mlclient.jobs import ReadDocumentsJob
from mlclient.models import Document, DocumentType, XMLDocument
from mlclient.models.http import DocumentsBodyPart as BodyPart
from tests.utils import filesystem as fs_utils
from tests.utils.ml_mockers import MLDocumentsMocker, MLRespXMocker

ml_doc_mocker = MLDocumentsMocker()

ml_mocker = MLRespXMocker(router_base_url="http://localhost:8000/v1/documents")
ml_mocker.with_get_side_effect(side_effect=ml_doc_mocker.get_documents_side_effect)


@ml_mocker.router
def test_basic_job_with_documents_output():
    with ml_doc_mocker.scoped():
        uris_count = 5
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(*_get_test_document_body_parts(uris_count))

        job = ReadDocumentsJob(batch_size=5)

        job.with_client_config(auth_method="digest")
        job.with_uris_input(uris)
        job.run_sync()
        docs = job.documents

    assert ml_mocker.router.calls.call_count == 1
    assert ml_mocker.router.calls.last.request.url.params.get("database") is None
    assert ml_mocker.router.calls.last.request.url.params.get("category") is None
    assert job.report.completed == uris_count
    assert job.report.successful == uris_count
    assert job.report.failed == 0
    _confirm_documents_data(uris, docs)


@ml_mocker.router
def test_basic_job_with_filesystem_output():
    with ml_doc_mocker.scoped():
        uris_count = 5
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(*_get_test_document_body_parts(uris_count))

        output_dir = str(Path(__file__).resolve().parent / "output")
        assert not Path(output_dir).exists()
        try:
            job = ReadDocumentsJob(batch_size=5)
            job.with_client_config(auth_method="digest")
            job.with_uris_input(uris)
            job.with_filesystem_output(output_dir)
            job.run_sync()

            assert ml_mocker.router.calls.call_count == 1
            assert (
                ml_mocker.router.calls.last.request.url.params.get("database") is None
            )
            assert (
                ml_mocker.router.calls.last.request.url.params.get("category") is None
            )
            assert job.report.completed == uris_count
            assert job.report.successful == uris_count
            assert job.report.failed == 0
            _confirm_filesystem_data(uris, output_dir)
        finally:
            fs_utils.safe_rmdir(output_dir)
            assert not Path(output_dir).exists()


@ml_mocker.router
def test_basic_job_with_multiple_inputs():
    with ml_doc_mocker.scoped():
        uris_count = 500
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(*_get_test_document_body_parts(uris_count))

        job = ReadDocumentsJob(batch_size=500)

        job.with_client_config(auth_method="digest")
        job.with_uris_input(uris[:250])
        job.with_uris_input(uris[250:])
        job.run_sync()
        docs = job.documents

        assert ml_mocker.router.calls.call_count == 1
        assert ml_mocker.router.calls.last.request.url.params.get("database") is None
        assert ml_mocker.router.calls.last.request.url.params.get("category") is None
        assert job.report.completed == uris_count
        assert job.report.successful == uris_count
        assert job.report.failed == 0
        _confirm_documents_data(uris, docs)


@ml_mocker.router
def test_job_with_documents_output_and_full_metadata():
    with ml_doc_mocker.scoped():
        uris_count = 5
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(
            *_get_test_document_body_parts(uris_count, metadata=["metadata"]),
        )

        job = ReadDocumentsJob(batch_size=5)

        job.with_client_config(auth_method="digest")
        job.with_uris_input(uris)
        job.with_metadata()
        job.run_sync()
        docs = job.documents

        assert ml_mocker.router.calls.call_count == 1
        assert ml_mocker.router.calls.last.request.url.params.get("database") is None
        assert ml_mocker.router.calls.last.request.url.params.get_list("category") == [
            "content",
            "metadata",
        ]
        assert job.report.completed == uris_count
        assert job.report.successful == uris_count
        assert job.report.failed == 0
        _confirm_documents_data(uris, docs, metadata=["metadata"])


@ml_mocker.router
def test_job_with_documents_output_and_some_metadata_categories():
    with ml_doc_mocker.scoped():
        uris_count = 5
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(
            *_get_test_document_body_parts(uris_count, metadata=["quality"]),
        )

        job = ReadDocumentsJob(batch_size=5)

        job.with_client_config(auth_method="digest")
        job.with_uris_input(uris)
        job.with_metadata("quality")
        job.run_sync()
        docs = job.documents

        assert ml_mocker.router.calls.call_count == 1
        assert ml_mocker.router.calls.last.request.url.params.get("database") is None
        assert ml_mocker.router.calls.last.request.url.params.get_list("category") == [
            "content",
            "quality",
        ]
        assert job.report.completed == uris_count
        assert job.report.successful == uris_count
        assert job.report.failed == 0
        _confirm_documents_data(uris, docs, metadata=["quality"])


@ml_mocker.router
def test_basic_job_with_filesystem_output_and_full_metadata():
    with ml_doc_mocker.scoped():
        uris_count = 5
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(
            *_get_test_document_body_parts(uris_count, metadata=["metadata"]),
        )

        output_dir = str(Path(__file__).resolve().parent / "output")
        assert not Path(output_dir).exists()
        try:
            job = ReadDocumentsJob(batch_size=5)
            job.with_client_config(auth_method="digest")
            job.with_uris_input(uris)
            job.with_metadata()
            job.with_filesystem_output(output_dir)
            job.run_sync()

            assert ml_mocker.router.calls.call_count == 1
            assert (
                ml_mocker.router.calls.last.request.url.params.get("database") is None
            )
            assert ml_mocker.router.calls.last.request.url.params.get_list(
                "category",
            ) == ["content", "metadata"]
            assert job.report.completed == uris_count
            assert job.report.successful == uris_count
            assert job.report.failed == 0
            _confirm_filesystem_data(uris, output_dir, metadata=["metadata"])
        finally:
            fs_utils.safe_rmdir(output_dir)
            assert not Path(output_dir).exists()


@ml_mocker.router
def test_basic_job_with_filesystem_output_and_some_metadata_categories():
    with ml_doc_mocker.scoped():
        uris_count = 5
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(
            *_get_test_document_body_parts(uris_count, metadata=["quality"]),
        )

        output_dir = str(Path(__file__).resolve().parent / "output")
        assert not Path(output_dir).exists()
        try:
            job = ReadDocumentsJob(batch_size=5)
            job.with_client_config(auth_method="digest")
            job.with_uris_input(uris)
            job.with_metadata("quality")
            job.with_filesystem_output(output_dir)
            job.run_sync()

            assert ml_mocker.router.calls.call_count == 1
            assert (
                ml_mocker.router.calls.last.request.url.params.get("database") is None
            )
            assert ml_mocker.router.calls.last.request.url.params.get_list(
                "category",
            ) == ["content", "quality"]
            assert job.report.completed == uris_count
            assert job.report.successful == uris_count
            assert job.report.failed == 0
            _confirm_filesystem_data(uris, output_dir, metadata=["quality"])
        finally:
            fs_utils.safe_rmdir(output_dir)
            assert not Path(output_dir).exists()


@ml_mocker.router
def test_job_with_custom_database():
    with ml_doc_mocker.scoped():
        uris_count = 5
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(*_get_test_document_body_parts(uris_count))

        job = ReadDocumentsJob(batch_size=5)

        job.with_client_config(auth_method="digest")
        job.with_database("Documents")
        job.with_uris_input(uris)
        job.run_sync()
        docs = job.documents

        assert ml_mocker.router.calls.call_count == 1
        assert (
            ml_mocker.router.calls.last.request.url.params.get("database")
            == "Documents"
        )
        assert ml_mocker.router.calls.last.request.url.params.get("category") is None
        assert job.report.completed == uris_count
        assert job.report.successful == uris_count
        assert job.report.failed == 0
        _confirm_documents_data(uris, docs)


@ml_mocker.router
def test_job_with_multiple_batches():
    with ml_doc_mocker.scoped():
        uris_count = 150
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(*_get_test_document_body_parts(uris_count))

        job = ReadDocumentsJob(batch_size=5)

        job.with_client_config(auth_method="digest")
        job.with_uris_input(uris)
        job.run_sync()
        docs = job.documents

        assert ml_mocker.router.calls.call_count == 30
        assert ml_mocker.router.calls.last.request.url.params.get("database") is None
        assert ml_mocker.router.calls.last.request.url.params.get("category") is None
        assert job.report.completed == uris_count
        assert job.report.successful == uris_count
        assert job.report.failed == 0
        _confirm_documents_data(uris, docs)


@respx.mock
def test_failing_job():
    uris_count = 5
    uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    for uri in uris:
        mocker.with_request_param("uri", uri)
    mocker.with_request_param("format", "json")
    mocker.with_response_content_type("application/json; charset=utf-8")
    mocker.with_response_code(401)
    mocker.with_response_body(
        {
            "errorResponse": {
                "statusCode": 401,
                "status": "Unauthorized",
                "message": "401 Unauthorized",
            },
        },
    )
    mocker.mock_get()

    job = ReadDocumentsJob(batch_size=5)
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.run_sync()
    docs = job.documents

    assert respx.calls.call_count == 1
    assert job.report.completed == uris_count
    assert job.report.successful == 0
    assert job.report.failed == uris_count
    for uri in uris:
        doc_report = job.report.get_doc_report(uri)
        assert doc_report.details.error == MarkLogicError
        assert doc_report.details.message == "[401 Unauthorized] 401 Unauthorized"
    assert len(docs) == 0


@ml_mocker.router
def test_failing_filesystem_write_step():
    with ml_doc_mocker.scoped():
        uris_count = 5
        uris = [f"/some/dir/doc{i + 1}.xml" for i in range(uris_count)]
        ml_doc_mocker.mock_document(*_get_test_document_body_parts(uris_count))

        output_dir_path = Path(__file__).resolve()
        assert output_dir_path.exists()
        try:
            job = ReadDocumentsJob(batch_size=5)
            job.with_client_config(auth_method="digest")
            job.with_uris_input(uris)
            job.with_filesystem_output(str(output_dir_path))
            job.run_sync()

            assert ml_mocker.router.calls.call_count == 1
            assert job.report.completed == uris_count
            assert job.report.successful == 0
            assert job.report.failed == uris_count

            dir_path = output_dir_path.absolute() / "some/dir"
            for uri in uris:
                doc_report = job.report.get_doc_report(uri)
                assert doc_report.details.error is NotADirectoryError
                assert (
                    doc_report.details.message
                    == f"[Errno 20] Not a directory: '{dir_path}'"
                )
        finally:
            assert output_dir_path.exists()


def _get_test_document_body_parts(
    count: int,
    *,
    start: int = 1,
    metadata: list[str] | None = None,
) -> Iterable[BodyPart]:
    range_start = start - 1
    range_end = start + count
    for i in range(range_start, range_end):
        yield from _get_test_document_body_part(i + 1, metadata)


def _get_test_document_body_part(
    num: int,
    metadata: list[str] | None = None,
) -> Iterable[BodyPart]:
    yield BodyPart(
        **{
            "content-type": "application/xml",
            "content-disposition": "attachment; "
            f'filename="/some/dir/doc{num}.xml"; '
            "category=content; "
            "format=xml",
            "content": '<?xml version="1.0" encoding="UTF-8"?>\n'
            f"<root><child>data{num}</child></root>",
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
        yield BodyPart(
            **{
                "content-type": "application/json",
                "content-disposition": "attachment; "
                f'filename="/some/dir/doc{num}.xml"; '
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
    for uri in uris:
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
        match = re.search(r"doc(\d+)\.xml$", uri)
        num = int(match.group(1))
        assert doc.content.getroot().tag == "root"
        assert doc.content.getroot().attrib == {}
        children = list(doc.content.getroot())
        assert len(children) == 1
        assert children[0].tag == "child"
        assert children[0].text == f"data{num}"
        assert children[0].attrib == {}


def _confirm_filesystem_data(
    uris: list[str],
    output_path: str,
    metadata: list[str] | None = None,
):
    assert Path(output_path).exists()
    expected_file_count = len(uris) * 2 if metadata else len(uris)
    assert (
        len([p for p in Path(output_path).rglob("*") if p.is_file()])
        == expected_file_count
    )
    for i, uri in enumerate(uris):
        file_path = Path(output_path) / uri[1:]
        assert file_path.exists()
        with file_path.open("r") as file:
            assert file.readlines() == [
                '<?xml version="1.0" encoding="UTF-8"?>\n',
                f"<root><child>data{i + 1}</child></root>",
            ]
        if metadata:
            metadata_file_path = file_path.with_suffix(".metadata.json")
            assert metadata_file_path.exists()
            with metadata_file_path.open("r") as metadata_file:
                doc_metadata = json.load(metadata_file)
            if "metadata" in metadata:
                metadata = [
                    "quality",
                    "collections",
                    "permissions",
                    "properties",
                    "metadata_values",
                ]
            assert "quality" not in metadata or doc_metadata["quality"] == 5
            assert "collections" not in metadata or doc_metadata["collections"] == [
                "test-collection",
            ]
            assert "permissions" not in metadata or doc_metadata["permissions"] == []
            assert "properties" not in metadata or doc_metadata["properties"] == {}
            assert (
                "metadata_values" not in metadata
                or doc_metadata["metadataValues"] == {}
            )
