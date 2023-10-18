from mlclient.model.calls import (DocumentsBodyPartType,
                                  DocumentsContentDisposition, Extract, Repair)


def test_to_str_inline():
    disp = DocumentsContentDisposition(
        body_part_type=DocumentsBodyPartType.INLINE,
        extension="jpeg",
        directory="/path/to/",
        repair=Repair.NONE,
        extract=Extract.DOCUMENT,
        version_id=1,
    )
    expected_str = ("inline; "
                    "extension=jpeg; "
                    "directory=/path/to/; "
                    "repair=none; "
                    "extract=document; "
                    "versionId=1")
    assert str(disp) == expected_str


def test_to_str_attachment():
    disp = DocumentsContentDisposition(
        body_part_type=DocumentsBodyPartType.ATTACHMENT,
        category="collections",
        filename="/path/to/file.xml",
        repair=Repair.FULL,
        temporal_document="/path/to/file.xml",
    )
    expected_str = ("attachment; "
                    "filename=/path/to/file.xml; "
                    "category=collections; "
                    "repair=full; "
                    "temporal-document=/path/to/file.xml")
    assert str(disp) == expected_str
