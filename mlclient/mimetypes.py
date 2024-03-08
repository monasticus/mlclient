"""The ML Client Mimetypes module.

This module extracts a class fetching mimetypes with file extensions and document types:

    * Mimetypes
        The Mimetypes utilities provider.
"""

from __future__ import annotations

from typing import ClassVar

import yaml

from mlclient import utils
from mlclient.structures import DocumentType, Mimetype


class Mimetypes:
    """The Mimetypes utilities provider.

    This class is not meant to be instantiated. It provides a set of useful static
    methods related to mimetypes in MarkLogic.
    """

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
        """Return all known mimetypes linked to a specific document type.

        Parameters
        ----------
        doc_type : DocumentType
            A document type to find mimetypes for

        Returns
        -------
        tuple[str]
            A tuple of mimetypes linked to a specific document type
        """
        cls._init_doc_type_mimetypes(doc_type)
        return tuple(
            mimetype.mime_type for mimetype in cls._DOC_TYPE_MIMETYPES[doc_type]
        )

    @classmethod
    def get_mimetype(
        cls,
        uri: str,
    ) -> str | None:
        """Return a mimetype linked to a specific extension.

        Parameters
        ----------
        uri : str
            A document uri, path or filename to find a mimetype for

        Returns
        -------
        str
            A mimetype linked to a specific extension
        """
        cls._init_mimetypes()
        gen = (
            mimetype.mime_type
            for mimetype in cls._MIMETYPES
            if uri.endswith(tuple(mimetype.extensions))
        )
        return next(gen, None)

    @classmethod
    def get_doc_type(
        cls,
        uri_or_mimetype: str,
    ) -> DocumentType:
        """Return a document type for a specific file or mime type.

        Parameters
        ----------
        uri_or_mimetype : str
            A document uri or mimetype to fetch a document type for

        Returns
        -------
        DocumentType
            A document type for a specific file or mime type
        """
        cls._init_mimetypes()
        for mimetype in cls._MIMETYPES:
            if uri_or_mimetype.startswith(
                mimetype.mime_type,
            ) or uri_or_mimetype.endswith(tuple(mimetype.extensions)):
                return mimetype.document_type
        return DocumentType.BINARY

    @classmethod
    def _init_doc_type_mimetypes(
        cls,
        doc_type: DocumentType,
    ):
        """Initialize mimetypes in an internal dictionary entry for a document type.

        Parameters
        ----------
        doc_type : DocumentType
            A document type to initialize mimetypes for
        """
        cls._init_mimetypes()
        if len(cls._DOC_TYPE_MIMETYPES[doc_type]) == 0:
            for mimetype in cls._MIMETYPES:
                if mimetype.document_type == doc_type:
                    cls._DOC_TYPE_MIMETYPES[doc_type].append(mimetype)

    @classmethod
    def _init_mimetypes(
        cls,
    ):
        """Initialize an internal list of mimetypes."""
        if cls._MIMETYPES is None:
            with utils.get_resource("mimetypes.yaml") as mimetypes_file:
                mimetypes_yaml = yaml.safe_load(mimetypes_file.read())
                mimetypes = mimetypes_yaml["mimetypes"]
                cls._MIMETYPES = [Mimetype(**mimetype) for mimetype in mimetypes]
