from mlclient.models import DocumentType
from mlclient.models.http import (
    DocumentsBodyPartType as BodyPartType,
    DocumentsDisposition as Disposition,
    Extract,
    Repair,
)


def test_from_header_inline():
    raw = (
        "inline; "
        "extension=jpeg; "
        "directory=/path/to/; "
        "repair=none; "
        "extract=document; "
        "versionId=1"
    )
    expected = Disposition(
        type=BodyPartType.INLINE,
        extension="jpeg",
        directory="/path/to/",
        repair=Repair.NONE,
        extract=Extract.DOCUMENT,
        version_id=1,
    )
    assert Disposition.from_header(raw) == expected


def test_from_header_attachment():
    raw = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )
    expected = Disposition(
        type=BodyPartType.ATTACHMENT,
        category="collections",
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )
    assert Disposition.from_header(raw) == expected


def test_from_header_multiple_categories():
    raw = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "category=quality; "
        "category=metadata-values; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )
    expected = Disposition(
        type=BodyPartType.ATTACHMENT,
        category=["collections", "quality", "metadata-values"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )
    assert Disposition.from_header(raw) == expected


def test_to_header_inline():
    disp = Disposition(
        type=BodyPartType.INLINE,
        extension="jpeg",
        directory="/path/to/",
        repair=Repair.NONE,
        extract=Extract.DOCUMENT,
        version_id=1,
    )
    expected = (
        "inline; "
        "extension=jpeg; "
        "directory=/path/to/; "
        "repair=none; "
        "extract=document; "
        "versionId=1"
    )
    assert disp.to_header() == expected


def test_to_header_attachment():
    disp = Disposition(
        type=BodyPartType.ATTACHMENT,
        category=["collections"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )
    expected = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )
    assert disp.to_header() == expected


def test_to_header_multiple_categories():
    disp = Disposition(
        type=BodyPartType.ATTACHMENT,
        category=["collections", "quality", "metadata-values"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )
    expected = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "category=quality; "
        "category=metadata-values; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )
    assert disp.to_header() == expected
