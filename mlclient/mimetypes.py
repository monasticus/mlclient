from __future__ import annotations

from typing import ClassVar

import yaml

from mlclient import utils
from mlclient.model import DocumentType, Mimetype


class Mimetypes:
    _MIMETYPES: ClassVar[list[Mimetype]] = None
    _DOC_TYPE_MIMETYPES: ClassVar[dict[DocumentType, list[Mimetype]]] = {
        DocumentType.XML: [],
        DocumentType.JSON: [],
        DocumentType.BINARY: [],
        DocumentType.TEXT: [],
    }

    @classmethod
    def get_mimetypes(
        cls,
        doc_type: DocumentType,
    ) -> tuple[str]:
        cls._init_doc_type_mimetypes(doc_type)
        return tuple(
            mimetype.mime_type for mimetype in cls._DOC_TYPE_MIMETYPES[doc_type]
        )

    @classmethod
    def get_doc_type(
        cls,
        uri_or_content_type: str,
    ):
        cls._init_mimetypes()
        for mimetype in cls._MIMETYPES:
            if uri_or_content_type.startswith(
                mimetype.mime_type,
            ) or uri_or_content_type.endswith(tuple(mimetype.extensions)):
                return mimetype.document_type
        return DocumentType.BINARY

    @classmethod
    def _init_doc_type_mimetypes(
        cls,
        doc_type: DocumentType,
    ):
        cls._init_mimetypes()
        if len(cls._DOC_TYPE_MIMETYPES[doc_type]) == 0:
            for mimetype in cls._MIMETYPES:
                if mimetype.document_type == doc_type:
                    cls._DOC_TYPE_MIMETYPES[doc_type].append(mimetype)

    @classmethod
    def _init_mimetypes(
        cls,
    ):
        if cls._MIMETYPES is None:
            with utils.get_resource("mimetypes.yaml") as mimetypes_file:
                mimetypes_yaml = yaml.safe_load(mimetypes_file.read())
                mimetypes = mimetypes_yaml["mimetypes"]
                cls._MIMETYPES = [Mimetype(**mimetype) for mimetype in mimetypes]
