from mlclient.constants import HEADER_JSON
from mlclient.models import DocumentType
from mlclient.models.http.documents import BodyPart, BodyPartType, Disposition, Repair


def test_parses_string_disposition_and_uses_default_content_type():
    body_part = BodyPart(
        **{
            "content-disposition": 'attachment; filename="/doc.json"; format=json',
            "content": {"key": "value"},
        },
    )

    assert body_part.content_type == HEADER_JSON
    assert body_part.disposition == Disposition(
        type=BodyPartType.ATTACHMENT,
        filename="/doc.json",
        format=DocumentType.JSON,
    )


def test_parses_dict_disposition():
    body_part = BodyPart(
        **{
            "content-type": "application/xml",
            "content-disposition": {
                "type": BodyPartType.INLINE,
                "extension": "xml",
                "directory": "/generated/",
                "repair": Repair.FULL,
            },
            "content": "<root/>",
        },
    )

    assert body_part.content_type == "application/xml"
    assert body_part.disposition == Disposition(
        type=BodyPartType.INLINE,
        extension="xml",
        directory="/generated/",
        repair=Repair.FULL,
    )
