from __future__ import annotations

import json

import pytest

from mlclient.io import DocumentsWriter
from mlclient.models import Document, Metadata


@pytest.mark.asyncio
async def test_write_document_content(tmp_path):
    doc = Document.create("/dir/doc-1.xml", "<root><child>data</child></root>")

    await DocumentsWriter.write_document(doc, str(tmp_path))

    written = tmp_path / "dir/doc-1.xml"
    assert written.read_bytes() == b"<root><child>data</child></root>"


@pytest.mark.asyncio
async def test_write_document_writes_json_content(tmp_path):
    doc = Document.create("/dir/doc-2.json", {"name": "Smith"})

    await DocumentsWriter.write_document(doc, str(tmp_path))

    written = tmp_path / "dir/doc-2.json"
    assert json.loads(written.read_text()) == {"name": "Smith"}


@pytest.mark.asyncio
async def test_write_document_with_raw_json_metadata(tmp_path):
    metadata = Metadata(raw=b'{"collections": ["some-collection"]}')
    doc = Document.create("/dir/doc-1.xml", "<root/>", metadata=metadata)

    await DocumentsWriter.write_document(doc, str(tmp_path))

    sidecar = tmp_path / "dir/doc-1.metadata.json"
    assert sidecar.exists()
    assert json.loads(sidecar.read_text()) == {"collections": ["some-collection"]}
    assert not (tmp_path / "dir/doc-1.metadata.xml").exists()


@pytest.mark.asyncio
async def test_write_document_with_raw_xml_metadata(tmp_path):
    raw = (
        b'<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">'
        b"<rapi:collections><rapi:collection>some-collection</rapi:collection>"
        b"</rapi:collections></rapi:metadata>"
    )
    metadata = Metadata(raw=raw)
    doc = Document.create("/dir/doc-1.xml", "<root/>", metadata=metadata)

    await DocumentsWriter.write_document(doc, str(tmp_path))

    sidecar = tmp_path / "dir/doc-1.metadata.xml"
    assert sidecar.read_bytes() == raw
    assert not (tmp_path / "dir/doc-1.metadata.json").exists()


@pytest.mark.asyncio
async def test_write_document_serializes_field_built_metadata_as_json(tmp_path):
    metadata = Metadata(collections=["some-collection"])
    doc = Document.create("/dir/doc-1.xml", "<root/>", metadata=metadata)

    await DocumentsWriter.write_document(doc, str(tmp_path))

    sidecar = tmp_path / "dir/doc-1.metadata.json"
    assert json.loads(sidecar.read_text())["collections"] == ["some-collection"]


@pytest.mark.asyncio
async def test_write_metadata_only_document_skips_content_file(tmp_path):
    metadata = Metadata(collections=["some-collection"])
    doc = Document.metadata_update("/dir/doc-1.xml", metadata)

    await DocumentsWriter.write_document(doc, str(tmp_path))

    assert not (tmp_path / "dir/doc-1.xml").exists()
    assert (tmp_path / "dir/doc-1.metadata.json").exists()


@pytest.mark.asyncio
async def test_write_documents(tmp_path):
    docs = [
        Document.create("/dir/doc-1.xml", "<root/>"),
        Document.create("/dir/doc-2.json", {"name": "Smith"}),
    ]

    await DocumentsWriter.write(docs, str(tmp_path))

    assert (tmp_path / "dir/doc-1.xml").exists()
    assert (tmp_path / "dir/doc-2.json").exists()


@pytest.mark.asyncio
async def test_write_document_creates_missing_directories(tmp_path):
    doc = Document.create("/deeply/nested/dir/doc-1.xml", "<root/>")

    await DocumentsWriter.write_document(doc, str(tmp_path))

    assert (tmp_path / "deeply/nested/dir/doc-1.xml").exists()
