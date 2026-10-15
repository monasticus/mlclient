from __future__ import annotations

import xml.etree.ElementTree as ElemTree
import zlib

import httpx
import pytest
import pytest_asyncio
import respx

from mlclient import AsyncMLClient
from mlclient.exceptions import MarkLogicError
from mlclient.models import (
    BinaryDocument,
    Category,
    Document,
    DocumentType,
    JSONDocument,
    Metadata,
    MetadataDocument,
    TextDocument,
    XMLDocument,
)
from mlclient.services.documents import _DocumentsSender
from tests.utils import data as test_data
from tests.utils import resources as resources_utils
from tests.utils.data import MetadataSpec
from tests.utils.ml_mockers import MLDocumentsMocker, MLRespXMocker

DOC_BODY_PARTS = [
    test_data.binary_doc_body_part("/some/dir/doc4.zip"),
    test_data.xml_doc_body_part("/some/dir/doc1.xml"),
    test_data.text_doc_body_part("/some/dir/doc3.xqy"),
    test_data.json_doc_body_part("/some/dir/doc2.json"),
]


ml_doc_mocker = MLDocumentsMocker(DOC_BODY_PARTS)

ml_mocker = MLRespXMocker(
    router_base_url="http://localhost:8000/v1/documents",
    strict_params=False,
)
ml_mocker.with_get_side_effect(side_effect=ml_doc_mocker.get_documents_side_effect)
ml_mocker.with_post_side_effect(side_effect=ml_doc_mocker.post_documents_side_effect)
ml_mocker.with_delete_side_effect(
    side_effect=ml_doc_mocker.delete_documents_side_effect,
)


@pytest_asyncio.fixture
async def svc():

    async with AsyncMLClient() as ml:
        yield ml.documents


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_non_existing_doc(svc):
    uri = "/some/dir/doc5.xml"

    with pytest.raises(MarkLogicError) as err:
        await svc.read(uri)

    expected_error = (
        "[404 Not Found] (RESTAPI-NODOCUMENT) "
        "RESTAPI-NODOCUMENT: (err:FOER0000) "
        "Resource or document does not exist:  "
        f"category: content message: {uri}"
    )
    assert err.value.args[0] == expected_error


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_xml_doc(svc):
    uri = "/some/dir/doc1.xml"

    document = await svc.read(uri)

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.doc_type == DocumentType.XML
    assert isinstance(document.content, ElemTree.ElementTree)
    assert document.content.getroot().tag == "root"
    assert document.metadata is None


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_xml_doc_using_uri_list(svc):
    uri = "/some/dir/doc1.xml"

    docs = await svc.read([uri])
    assert isinstance(docs, dict)
    assert len(docs) == 1

    document = docs[uri]
    assert isinstance(document, XMLDocument)
    assert document.uri == uri


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_json_doc(svc):
    uri = "/some/dir/doc2.json"

    document = await svc.read(uri)

    assert isinstance(document, JSONDocument)
    assert document.uri == uri
    assert document.content == {"root": {"child": "data"}}


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_text_doc(svc):
    uri = "/some/dir/doc3.xqy"

    document = await svc.read(uri)

    assert isinstance(document, TextDocument)
    assert document.uri == uri
    assert document.content == 'xquery version "1.0-ml";\n\nfn:current-date()'


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_binary_doc(svc):
    uri = "/some/dir/doc4.zip"
    content = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()')

    document = await svc.read(uri)

    assert isinstance(document, BinaryDocument)
    assert document.uri == uri
    assert document.content == content


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_multiple_docs(svc):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    docs = await svc.read(uris)

    assert isinstance(docs, dict)
    assert len(docs) == 4
    assert isinstance(docs["/some/dir/doc1.xml"], XMLDocument)
    assert isinstance(docs["/some/dir/doc2.json"], JSONDocument)
    assert isinstance(docs["/some/dir/doc3.xqy"], TextDocument)
    assert isinstance(docs["/some/dir/doc4.zip"], BinaryDocument)


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_multiple_non_existing_docs(svc):
    uris = [
        "/some/dir/doc5.xml",
        "/some/dir/doc6.xml",
    ]

    docs = await svc.read(uris)

    assert docs == {}


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_doc_with_full_metadata(svc):
    with ml_doc_mocker.scoped(fresh=False):
        ml_doc_mocker.mock_document(
            test_data.doc_full_metadata_body_part(
                "/some/dir/doc1.xml",
                MetadataSpec(collections=["xml"]),
                metadata_category=True,
            ),
        )
        uri = "/some/dir/doc1.xml"

        document = await svc.read(uri, category=["content", "metadata"])

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_full_metadata_without_content(svc):
    with ml_doc_mocker.scoped(fresh=False):
        ml_doc_mocker.mock_document(
            test_data.doc_full_metadata_body_part(
                "/some/dir/doc1.xml",
                MetadataSpec(collections=["xml"]),
                metadata_category=True,
            ),
        )
        uri = "/some/dir/doc1.xml"

        document = await svc.read(uri, category=["metadata"])

    assert isinstance(document, MetadataDocument)
    assert document.uri == uri
    assert document.content is None
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_doc_with_full_metadata_using_category_enum(svc):
    with ml_doc_mocker.scoped(fresh=False):
        ml_doc_mocker.mock_document(
            test_data.doc_full_metadata_body_part(
                "/some/dir/doc1.xml",
                MetadataSpec(collections=["xml"]),
                metadata_category=True,
            ),
        )
        uri = "/some/dir/doc1.xml"

        document = await svc.read(
            uri,
            category=[Category.CONTENT, Category.METADATA],
        )

    assert isinstance(document, XMLDocument)
    assert document.uri == uri
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_full_metadata_without_content_using_category_enum(svc):
    with ml_doc_mocker.scoped(fresh=False):
        ml_doc_mocker.mock_document(
            test_data.doc_full_metadata_body_part(
                "/some/dir/doc1.xml",
                MetadataSpec(collections=["xml"]),
                metadata_category=True,
            ),
        )
        uri = "/some/dir/doc1.xml"

        document = await svc.read(uri, category=[Category.METADATA])

    assert isinstance(document, MetadataDocument)
    assert document.uri == uri
    assert document.content is None
    assert document.metadata is not None
    assert document.metadata.collections() == ["xml"]


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_single_doc_using_custom_database(svc):
    uri = "/some/dir/doc1.xml"

    document = await svc.read(uri, database="Documents")

    assert isinstance(document, XMLDocument)
    assert document.uri == uri


@pytest.mark.asyncio
@respx.mock
async def test_read_forwards_txid(svc):
    uri = "/some/dir/doc1.xml"

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_request_param("txid", "txn-123")
    mocker.with_request_param("format", "json")
    mocker.with_get_side_effect(side_effect=ml_doc_mocker.get_documents_side_effect)

    await svc.read(uri, txid="txn-123")


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_stream_single_uri(svc):
    uri = "/some/dir/doc1.xml"

    docs = [doc async for doc in svc.read_stream([uri])]

    assert len(docs) == 1
    assert isinstance(docs[0], XMLDocument)
    assert docs[0].uri == uri


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_stream_multiple_uris(svc):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
        "/some/dir/doc3.xqy",
        "/some/dir/doc4.zip",
    ]

    docs = [doc async for doc in svc.read_stream(uris)]

    assert len(docs) == 4


@pytest.mark.asyncio
@ml_mocker.router
async def test_create_xml_document_from_bytes(svc):
    uri = "/some/dir/doc1.xml"
    content = b"<root><child>data</child></root>"
    doc = XMLDocument(content, uri)

    resp = await svc.write(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri
    assert documents[0]["mime-type"] == "application/xml"


@pytest.mark.asyncio
@ml_mocker.router
async def test_create_xml_document(svc):
    uri = "/some/dir/doc1.xml"
    content_str = "<root><child>data</child></root>"
    content = ElemTree.ElementTree(ElemTree.fromstring(content_str))
    doc = XMLDocument(content, uri)

    resp = await svc.write(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri


@pytest.mark.asyncio
@ml_mocker.router
async def test_create_json_document(svc):
    uri = "/some/dir/doc2.json"
    content = {"root": {"child": "data"}}
    doc = JSONDocument(content, uri)

    resp = await svc.write(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri


@pytest.mark.asyncio
@ml_mocker.router
async def test_create_multiple_documents(svc):
    doc_1 = XMLDocument(
        ElemTree.ElementTree(ElemTree.fromstring("<root/>")),
        "/some/dir/doc1.xml",
    )
    doc_2 = JSONDocument({"root": {"child": "data"}}, "/some/dir/doc2.json")

    resp = await svc.write([doc_1, doc_2])

    documents = resp["documents"]
    assert len(documents) == 2


@pytest.mark.asyncio
@ml_mocker.router
async def test_create_document_with_metadata(svc):
    uri = "/some/dir/doc1.xml"
    content_str = "<root><child>data</child></root>"
    content = ElemTree.ElementTree(ElemTree.fromstring(content_str))
    metadata = Metadata(collections=["test-collection"])
    doc = XMLDocument(content, uri, metadata)

    resp = await svc.write(doc)

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri


@pytest.mark.asyncio
@ml_mocker.router
async def test_create_metadata_document_when_doc_does_not_exist(svc):
    uri = f"/some/dir/{MLDocumentsMocker.NON_EXISTING_TAG}-doc.xml"
    metadata = Metadata(collections=["test-collection"])
    doc = MetadataDocument(uri, metadata)

    with pytest.raises(MarkLogicError) as err:
        await svc.write(doc)

    expected_error = (
        "[404 Not Found] (XDMP-DOCNOTFOUND) XDMP-DOCNOTFOUND: "
        f'xdmp:document-set-collections("{uri}", "test-collection")'
        " -- Document not found"
    )
    assert err.value.args[0] == expected_error


@pytest.mark.asyncio
@ml_mocker.router
async def test_create_document_with_temporal_collection(svc):
    uri = "/some/dir/doc1.xml"
    content = "<root><child>data</child><systemStart/><systemEnd/></root>"
    doc = XMLDocument(content, uri)

    resp = await svc.write(doc, temporal_collection="temporal-collection")

    documents = resp["documents"]
    assert len(documents) == 1
    assert documents[0]["uri"] == uri


@pytest.mark.asyncio
@respx.mock
async def test_write_forwards_txid(svc):
    doc = XMLDocument(b"<root/>", "/some/dir/doc1.xml")

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("txid", "txn-123")
    mocker.with_post_side_effect(side_effect=ml_doc_mocker.post_documents_side_effect)

    await svc.write(doc, txid="txn-123")


@pytest.mark.asyncio
@respx.mock
async def test_delete_preserves_bodyless_http_failure(svc):
    route = respx.delete(
        "http://localhost:8000/v1/documents",
        params={"uri": "/example.json"},
    ).respond(403)

    with pytest.raises(httpx.HTTPStatusError) as raised:
        await svc.delete("/example.json")

    assert route.call_count == 1
    assert raised.value.response.url == route.calls.last.request.url
    assert raised.value.response.status_code == 403


@pytest.mark.asyncio
@respx.mock
async def test_delete_single_document(svc):
    uri = "/some/dir/doc1.xml"

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.mock_delete()

    try:
        await svc.delete(uri)
    except MarkLogicError as err:
        pytest.fail(str(err))


@pytest.mark.asyncio
@respx.mock
async def test_delete_multiple_documents(svc):
    uris = [
        "/some/dir/doc1.xml",
        "/some/dir/doc2.json",
    ]

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    for uri in uris:
        mocker.with_request_param("uri", uri)
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.mock_delete()

    try:
        await svc.delete(uris)
    except MarkLogicError as err:
        pytest.fail(str(err))


@pytest.mark.asyncio
@respx.mock
async def test_delete_batches_preserve_request_timeout(svc):
    uris = [f"/{index}-" + "x" * 1024 for index in range(60)]
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    route = mocker.mock_delete()

    await svc.delete(uris, timeout=2)

    assert route.call_count > 1
    assert all(
        call.request.extensions["timeout"] == httpx.Timeout(2).as_dict()
        for call in route.calls
    )


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_with_category(svc):
    uri = "/some/dir/doc1.xml"

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_request_param("category", "collections")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.mock_delete()

    try:
        await svc.delete(uri, category="collections")
    except MarkLogicError as err:
        pytest.fail(str(err))


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_with_category_enum(svc):
    uri = "/some/dir/doc1.xml"

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_request_param("category", "collections")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.mock_delete()

    try:
        await svc.delete(uri, category=Category.COLLECTIONS)
    except MarkLogicError as err:
        pytest.fail(str(err))


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_with_custom_database(svc):
    uri = "/some/dir/doc1.xml"

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_request_param("database", "Documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.mock_delete()

    try:
        await svc.delete(uri, database="Documents")
    except MarkLogicError as err:
        pytest.fail(str(err))


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_with_temporal_collection(svc):
    uri = "/some/dir/doc1.xml"

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_request_param("temporal-collection", "temporal-collection")
    mocker.with_response_header(
        "x-marklogic-system-time",
        "2023-11-28T06:46:51.297376Z",
    )
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.mock_delete()

    try:
        await svc.delete(uri, temporal_collection="temporal-collection")
    except MarkLogicError as err:
        pytest.fail(str(err))


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_with_wipe_temporal(svc):
    uri = "/some/dir/doc1.xml"

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_request_param("temporal-collection", "temporal-collection")
    mocker.with_request_param("result", "wiped")
    mocker.with_response_header(
        "x-marklogic-system-time",
        "2023-11-28T09:02:48.09751Z",
    )
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.mock_delete()

    try:
        await svc.delete(
            uri,
            temporal_collection="temporal-collection",
            wipe_temporal=True,
        )
    except MarkLogicError as err:
        pytest.fail(str(err))


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_with_non_existing_database(svc):
    uri = "/some/dir/doc1.xml"

    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-delete-document-with-non-existing-database.xml",
    )

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_request_param("database", "Document")
    mocker.with_response_content_type("application/xml; charset=UTF-8")
    mocker.with_response_code(404)
    mocker.with_response_body(response_body)
    mocker.mock_delete()

    with pytest.raises(MarkLogicError) as err:
        await svc.delete(uri, database="Document")

    expected_error = (
        "[404 Not Found] (XDMP-NOSUCHDB) XDMP-NOSUCHDB: No such database Document"
    )
    assert err.value.args[0] == expected_error


@pytest.mark.asyncio
@respx.mock
async def test_delete_forwards_txid(svc):
    uri = "/some/dir/doc1.xml"

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", uri)
    mocker.with_request_param("txid", "txn-123")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.mock_delete()

    try:
        await svc.delete(uri, txid="txn-123")
    except MarkLogicError as err:
        pytest.fail(str(err))


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_stream_single_uri_is_not_batched(svc):
    uri = "/some/dir/doc1.xml"

    docs = [doc async for doc in svc.read_stream(uri)]

    assert len(docs) == 1
    assert ml_mocker.router.calls.call_count == 1


@pytest.mark.asyncio
@ml_mocker.router
async def test_read_stream_many_uris_are_batched(svc):
    uris = [f"/some/dir/doc{i:04d}.xml" for i in range(2000)]
    with ml_doc_mocker.scoped():
        ml_doc_mocker.mock_document(*(test_data.xml_doc_body_part(uri) for uri in uris))

        docs = [doc async for doc in svc.read_stream(uris)]

    assert len(docs) == 2000
    assert ml_mocker.router.calls.call_count > 1


@pytest.mark.asyncio
@ml_mocker.router
async def test_delete_single_uri_is_not_batched(svc):
    uri = "/some/dir/doc1.xml"

    await svc.delete(uri)

    assert ml_mocker.router.calls.call_count == 1


@pytest.mark.asyncio
@ml_mocker.router
async def test_delete_many_uris_are_batched(svc):
    uris = [f"/some/dir/doc{i:04d}.xml" for i in range(2000)]

    await svc.delete(uris)

    assert ml_mocker.router.calls.call_count > 1


# --- _DocumentsSender unit tests ---


def test_documents_sender_metadata_document_with_raw_bytes_metadata():
    doc = MetadataDocument("/x.xml", b'{"collections": ["c1"]}')
    parts = _DocumentsSender.parse(doc)

    assert len(parts) == 1
    assert parts[0].content == '{"collections": ["c1"]}'


def test_documents_sender_metadata_document_with_raw_str_metadata():
    doc = MetadataDocument("/x.xml", '{"collections": ["c1"]}')
    parts = _DocumentsSender.parse(doc)

    assert len(parts) == 1
    assert parts[0].content == '{"collections": ["c1"]}'


def test_documents_sender_metadata_document_with_metadata_object():
    doc = MetadataDocument("/x.xml", Metadata(collections=["c1"]))
    parts = _DocumentsSender.parse(doc)

    assert len(parts) == 1
    assert '"collections"' in parts[0].content


@pytest.mark.asyncio
@respx.mock
async def test_read_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents
        result = await documents.read("/some/dir/doc1.xml")

    assert result.uri == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_read_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents
        result = await documents.read(
            "/some/dir/doc1.xml",
            database="request-db",
            txid="request-tx",
        )

    assert result.uri == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_read_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = await documents.read("/some/dir/doc1.xml")

    assert result.uri == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_read_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = await documents.read(
            "/some/dir/doc1.xml",
            database="request-db",
            txid="request-tx",
        )

    assert result.uri == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_read_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = await documents.read("/some/dir/doc1.xml", database=None)

    assert result.uri == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_read_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("database", "service-db")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = await documents.read("/some/dir/doc1.xml", txid=None)

    assert result.uri == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_read_stream_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents
        result = [doc async for doc in documents.read_stream("/some/dir/doc1.xml")]

    assert [doc.uri for doc in result] == ["/some/dir/doc1.xml"]


@pytest.mark.asyncio
@respx.mock
async def test_read_stream_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents
        result = [
            doc
            async for doc in documents.read_stream(
                "/some/dir/doc1.xml",
                database="request-db",
                txid="request-tx",
            )
        ]

    assert [doc.uri for doc in result] == ["/some/dir/doc1.xml"]


@pytest.mark.asyncio
@respx.mock
async def test_read_stream_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = [doc async for doc in documents.read_stream("/some/dir/doc1.xml")]

    assert [doc.uri for doc in result] == ["/some/dir/doc1.xml"]


@pytest.mark.asyncio
@respx.mock
async def test_read_stream_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = [
            doc
            async for doc in documents.read_stream(
                "/some/dir/doc1.xml",
                database="request-db",
                txid="request-tx",
            )
        ]

    assert [doc.uri for doc in result] == ["/some/dir/doc1.xml"]


@pytest.mark.asyncio
@respx.mock
async def test_read_stream_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = [
            doc
            async for doc in documents.read_stream("/some/dir/doc1.xml", database=None)
        ]

    assert [doc.uri for doc in result] == ["/some/dir/doc1.xml"]


@pytest.mark.asyncio
@respx.mock
async def test_read_stream_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("database", "service-db")
    mocker.with_get_side_effect(ml_doc_mocker.get_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = [
            doc async for doc in documents.read_stream("/some/dir/doc1.xml", txid=None)
        ]

    assert [doc.uri for doc in result] == ["/some/dir/doc1.xml"]


@pytest.mark.asyncio
@respx.mock
async def test_write_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_post_side_effect(ml_doc_mocker.post_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents
        result = await documents.write(
            Document.create("/some/dir/doc1.xml", "<root/>"),
        )

    assert result["documents"][0]["uri"] == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_write_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_post_side_effect(ml_doc_mocker.post_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents
        result = await documents.write(
            Document.create("/some/dir/doc1.xml", "<root/>"),
            database="request-db",
            txid="request-tx",
        )

    assert result["documents"][0]["uri"] == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_write_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_post_side_effect(ml_doc_mocker.post_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = await documents.write(
            Document.create("/some/dir/doc1.xml", "<root/>"),
        )

    assert result["documents"][0]["uri"] == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_write_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.with_post_side_effect(ml_doc_mocker.post_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = await documents.write(
            Document.create("/some/dir/doc1.xml", "<root/>"),
            database="request-db",
            txid="request-tx",
        )

    assert result["documents"][0]["uri"] == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_write_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("txid", "service-tx")
    mocker.with_post_side_effect(ml_doc_mocker.post_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = await documents.write(
            Document.create("/some/dir/doc1.xml", "<root/>"),
            database=None,
        )

    assert result["documents"][0]["uri"] == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_write_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_request_param("database", "service-db")
    mocker.with_post_side_effect(ml_doc_mocker.post_documents_side_effect)

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        result = await documents.write(
            Document.create("/some/dir/doc1.xml", "<root/>"),
            txid=None,
        )

    assert result["documents"][0]["uri"] == "/some/dir/doc1.xml"


@pytest.mark.asyncio
@respx.mock
async def test_delete_without_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.mock_delete()

    async with AsyncMLClient() as ml:
        documents = ml.documents
        await documents.delete("/some/dir/doc1.xml")


@pytest.mark.asyncio
@respx.mock
async def test_delete_with_scope_kwargs():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_delete()

    async with AsyncMLClient() as ml:
        documents = ml.documents
        await documents.delete(
            "/some/dir/doc1.xml",
            database="request-db",
            txid="request-tx",
        )


@pytest.mark.asyncio
@respx.mock
async def test_delete_inherits_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("database", "service-db")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_delete()

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        await documents.delete("/some/dir/doc1.xml")


@pytest.mark.asyncio
@respx.mock
async def test_delete_scope_kwargs_override_service_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("database", "request-db")
    mocker.with_request_param("txid", "request-tx")
    mocker.mock_delete()

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        await documents.delete(
            "/some/dir/doc1.xml",
            database="request-db",
            txid="request-tx",
        )


@pytest.mark.asyncio
@respx.mock
async def test_delete_scope_kwargs_clear_service_database():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("txid", "service-tx")
    mocker.mock_delete()

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        await documents.delete("/some/dir/doc1.xml", database=None)


@pytest.mark.asyncio
@respx.mock
async def test_delete_scope_kwargs_clear_service_transaction():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("database", "service-db")
    mocker.mock_delete()

    async with AsyncMLClient() as ml:
        documents = ml.documents(database="service-db", txid="service-tx")
        await documents.delete("/some/dir/doc1.xml", txid=None)


@pytest.mark.asyncio
@respx.mock
async def test_overriding_scope_on_service_copy_preserves_original_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.mock_delete()
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-2")
    mocker.mock_delete()

    async with AsyncMLClient() as ml:
        original_service = ml.documents(database="catalog", txid="tx-1")
        overridden_scope_service = original_service(txid="tx-2")
        await overridden_scope_service.delete("/some/dir/doc1.xml")
        await original_service.delete("/some/dir/doc1.xml")


@pytest.mark.asyncio
@respx.mock
async def test_clearing_scope_on_service_copy_preserves_original_scope():
    mocker = MLRespXMocker(use_router=False, strict_params=True)
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.with_request_param("database", "catalog")
    mocker.with_request_param("txid", "tx-1")
    mocker.mock_delete()
    mocker.with_url("http://localhost:8000/v1/documents")
    mocker.with_response_code(204)
    mocker.with_empty_response_body()
    mocker.with_request_param("uri", "/some/dir/doc1.xml")
    mocker.mock_delete()

    async with AsyncMLClient() as ml:
        original_service = ml.documents(database="catalog", txid="tx-1")
        cleared_scope_service = original_service(database=None, txid=None)
        await cleared_scope_service.delete("/some/dir/doc1.xml")
        await original_service.delete("/some/dir/doc1.xml")
