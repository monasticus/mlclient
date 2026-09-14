from mlclient._constants import HEADER_JSON
from mlclient.models import (
    DocumentsBodyPart,
    DocumentsBodyPartType,
    DocumentsDisposition,
    DocumentType,
    Repair,
)


def test_parses_string_disposition_and_uses_default_content_type():
    body_part = DocumentsBodyPart(
        **{
            "content-disposition": 'attachment; filename="/doc.json"; format=json',
            "content": {"key": "value"},
        },
    )

    assert body_part.content_type == HEADER_JSON
    assert body_part.disposition == DocumentsDisposition(
        type=DocumentsBodyPartType.ATTACHMENT,
        filename="/doc.json",
        format=DocumentType.JSON,
    )


def test_parses_dict_disposition():
    body_part = DocumentsBodyPart(
        **{
            "content-type": "application/xml",
            "content-disposition": {
                "type": DocumentsBodyPartType.INLINE,
                "extension": "xml",
                "directory": "/generated/",
                "repair": Repair.FULL,
            },
            "content": "<root/>",
        },
    )

    assert body_part.content_type == "application/xml"
    assert body_part.disposition == DocumentsDisposition(
        type=DocumentsBodyPartType.INLINE,
        extension="xml",
        directory="/generated/",
        repair=Repair.FULL,
    )
