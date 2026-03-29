from mlclient.models import DocumentType
from mlclient.models.http.documents import (
    BodyPartType,
    Category,
    Disposition,
    Extract,
    Repair,
)


def test_from_header_for_inline():
    raw = (
        "inline; "
        "extension=jpeg; "
        "directory=/path/to/; "
        "repair=none; "
        "extract=document; "
        "versionId=1"
    )

    assert Disposition.from_header(raw) == Disposition(
        type=BodyPartType.INLINE,
        extension="jpeg",
        directory="/path/to/",
        repair=Repair.NONE,
        extract=Extract.DOCUMENT,
        version_id=1,
    )


def test_from_header_for_attachment():
    raw = (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )

    assert Disposition.from_header(raw) == Disposition(
        type=BodyPartType.ATTACHMENT,
        category="collections",
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )


def test_from_header_for_multiple_categories():
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

    assert Disposition.from_header(raw) == Disposition(
        type=BodyPartType.ATTACHMENT,
        category=["collections", "quality", "metadata-values"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )


def test_is_attachment_false_for_inline():
    disposition = Disposition(type=BodyPartType.INLINE)

    assert disposition.is_inline is True
    assert disposition.is_attachment is False


def test_is_inline_false_for_attachment():
    disposition = Disposition(type=BodyPartType.ATTACHMENT)

    assert disposition.is_attachment is True
    assert disposition.is_inline is False


def test_parse_header_part_maps_aliases_and_strips_filename_quotes():
    assert Disposition._parse_header_part("attachment") == ("type_", "attachment")
    assert Disposition._parse_header_part('filename="/doc.xml"') == (
        "filename",
        "/doc.xml",
    )
    assert Disposition._parse_header_part("format=json") == ("format", "json")


def test_serialize_field_returns_none_for_missing_value():
    disposition = Disposition(type=BodyPartType.ATTACHMENT)

    assert disposition._serialize_field("directory") is None


def test_to_header_for_inline():
    disposition = Disposition(
        type=BodyPartType.INLINE,
        extension="jpeg",
        directory="/path/to/",
        repair=Repair.NONE,
        extract=Extract.DOCUMENT,
        version_id=1,
    )

    assert disposition.to_header() == (
        "inline; "
        "extension=jpeg; "
        "directory=/path/to/; "
        "repair=none; "
        "extract=document; "
        "versionId=1"
    )


def test_to_header_for_attachment():
    disposition = Disposition(
        type=BodyPartType.ATTACHMENT,
        category=["collections"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )

    assert disposition.to_header() == (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )


def test_to_header_for_multiple_categories():
    disposition = Disposition(
        type=BodyPartType.ATTACHMENT,
        category=["collections", "quality", "metadata-values"],
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
        format=DocumentType.JSON,
    )

    assert disposition.to_header() == (
        "attachment; "
        'filename="/path/to/file.xml"; '
        "category=collections; "
        "category=quality; "
        "category=metadata-values; "
        "repair=full; "
        "temporal-document=/path/to/file.xml; "
        "format=json"
    )


def test_serialize_field_uses_enum_values_and_quotes_filename():
    disposition = Disposition(
        type=BodyPartType.ATTACHMENT,
        filename="/doc.xml",
        category=[Category.COLLECTIONS, Category.QUALITY],
        extract=Extract.PROPERTIES,
    )

    assert disposition._serialize_field("filename") == 'filename="/doc.xml"'
    assert disposition._serialize_field("category") == "category=collections; category=quality"
    assert disposition._serialize_field("extract") == "extract=properties"
