from __future__ import annotations

from typing import ClassVar

import yaml

from mlclient import utils
from mlclient.model import DocumentType, Mimetype


class Mimetypes:
    _MIMETYPES: ClassVar[list[Mimetype]] = None
    _DOC_TYPE_MIMETYPES: ClassVar[dict] = {
        DocumentType.XML: [],
        DocumentType.JSON: [],
        DocumentType.BINARY: [],
        DocumentType.TEXT: [],
    }

    @classmethod
    def get_mimetypes(
            cls,
            doc_type: DocumentType,
    ) -> list[str]:
        if cls._MIMETYPES is None:
            cls._init_mimetypes()
        if len(cls._DOC_TYPE_MIMETYPES[doc_type]) == 0:
            cls._init_doc_type_mimetypes(doc_type)

        return [mimetype.mime_type for mimetype in cls._DOC_TYPE_MIMETYPES[doc_type]]

    @classmethod
    def _init_mimetypes(
            cls,
    ):
        with utils.get_resource("mimetypes.yaml") as mimetypes_file:
            constants = yaml.safe_load(mimetypes_file.read())
            mimetypes = constants["mimetypes"]
            cls._MIMETYPES = [Mimetype(**mimetype) for mimetype in mimetypes]

    @classmethod
    def _init_doc_type_mimetypes(
            cls,
            doc_type: DocumentType,
    ):
        for mimetype in cls._MIMETYPES:
            if mimetype.document_type == doc_type:
                cls._DOC_TYPE_MIMETYPES[doc_type].append(mimetype)
