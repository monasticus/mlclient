from mlclient.calls.model import (
    ContentDispositionSerializer,
    DocumentsBodyPartType,
    DocumentsContentDisposition,
    Extract,
    Repair,
)
from mlclient.structures import DocumentType


def test_serialize_inline():
    raw_content_disposition = (
        "inline; "
        "extension=jpeg; "
        "directory=/path/to/; "
        "repair=none; "
        "extract=document; "
        "versionId=1"
    )
    expected_disp = DocumentsContentDisposition(
        body_part_type=DocumentsBodyPartType.INLINE,
        extension="jpeg",
        directory="/path/to/",
        repair=Repair.NONE,
        extract=Extract.DOCUMENT,
        version_id=1,
    )
    actual_disp = ContentDispositionSerializer.serialize(raw_content_disposition)
    assert actual_disp == expected_disp


def test_serialize_attachment():
    raw_content_disposition = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )
    expected_disp = DocumentsContentDisposition(
        body_part_type=DocumentsBodyPartType.ATTACHMENT,
        category="collections",
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )
    actual_disp = ContentDispositionSerializer.serialize(raw_content_disposition)
    assert actual_disp == expected_disp


def test_serialize_multiple_categories():
    raw_content_disposition = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "category=quality; "
        "category=metadata-values; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )
    expected_disp = DocumentsContentDisposition(
        body_part_type=DocumentsBodyPartType.ATTACHMENT,
        category=["collections", "quality", "metadata-values"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )
    actual_disp = ContentDispositionSerializer.serialize(raw_content_disposition)
    assert actual_disp == expected_disp


def test_deserialize_inline():
    disp = DocumentsContentDisposition(
        body_part_type=DocumentsBodyPartType.INLINE,
        extension="jpeg",
        directory="/path/to/",
        repair=Repair.NONE,
        extract=Extract.DOCUMENT,
        version_id=1,
    )
    expected_str = (
        "inline; "
        "extension=jpeg; "
        "directory=/path/to/; "
        "repair=none; "
        "extract=document; "
        "versionId=1"
    )
    actual_str = ContentDispositionSerializer.deserialize(disp)
    assert actual_str == expected_str


def test_deserialize_attachment():
    disp = DocumentsContentDisposition(
        body_part_type=DocumentsBodyPartType.ATTACHMENT,
        category=["collections"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )
    expected_str = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )
    actual_str = ContentDispositionSerializer.deserialize(disp)
    assert actual_str == expected_str


def test_deserialize_multiple_categories():
    disp = DocumentsContentDisposition(
        body_part_type=DocumentsBodyPartType.ATTACHMENT,
        category=["collections", "quality", "metadata-values"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )
    expected_str = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "category=quality; "
        "category=metadata-values; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )
    actual_str = ContentDispositionSerializer.deserialize(disp)
    assert actual_str == expected_str
