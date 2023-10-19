"""The Documents Call Model module.

This module contains an API for /v1/documents call body.
It exports the following classes:

    * DocumentsBodyPart
        A class representing /v1/documents body part.
    * DocumentsContentDisposition
        A class representing /v1/documents body part Content-Disposition header.
    * DocumentsBodyPartType
        An enumeration class representing /v1/documents body part types.
    * Repair
        An enumeration class representing repair levels.
    * Extract
        An enumeration class representing metadata extract types.
    * Category
        An enumeration class representing data categories.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field

from mlclient.constants import HEADER_JSON
from mlclient.model import DocumentType


class DocumentsBodyPartType(Enum):
    """An enumeration class representing /v1/documents body part types."""

    INLINE = "inline"
    ATTACHMENT = "attachment"


class Repair(Enum):
    """An enumeration class representing repair levels."""

    NONE = "none"
    FULL = "full"


class Extract(Enum):
    """An enumeration class representing metadata extract types."""

    PROPERTIES = "properties"
    DOCUMENT = "document"


class Category(Enum):
    """An enumeration class representing data categories."""

    CONTENT = "content"
    METADATA = "metadata"
    METADATA_VALUES = "metadata-values"
    COLLECTIONS = "collections"
    PERMISSIONS = "permissions"
    PROPERTIES = "properties"
    QUALITY = "quality"


class DocumentsContentDisposition(BaseModel):
    """A class representing /v1/documents body part Content-Disposition header."""

    body_part_type: DocumentsBodyPartType = Field(
        description="The content type indication (inline or attachment).")
    category: Optional[Category] = Field(
        description="The category of data.",
        default=None)
    repair: Optional[Repair] = Field(
        description="For an XML content part, the level of XML repair to perform. "
                    "Allowed values: full (default) or none. "
                    "Use full to request the server to repair malformed input XML. "
                    "Use none to request the server to reject malformed input XML. "
                    "If repair results in multiple root nodes, the update is rejected.",
        default=None)
    filename: Optional[str] = Field(
        description="Specifies an explicit document URI. "
                    "Use extension to have MarkLogic Server generate a URI instead. "
                    "For a given part, filename and extension are mutually exclusive.",
        default=None)
    extension: Optional[str] = Field(
        description="Specifies a URI extension to use when the document URI "
                    "is generated by MarkLogic Server. "
                    "The generated URI will end with '.' plus this extension. "
                    "For a given part, filename and extension are mutually exclusive.",
        default=None)
    directory: Optional[str] = Field(
        description="Specifies a directory prefix to use when the document URI "
                    "is generated by MarkLogic Server. "
                    "The directory prefix must end with '/'. "
                    "If the part header includes a directory parameter, "
                    "it must also include an extension parameter. "
                    "For a given part, filename and directory are mutually exclusive.",
        default=None)
    extract: Optional[Extract] = Field(
        description="For a binary content part, whether or not to extract metadata, "
                    "and whether to store the extracted metadata as document properties"
                    "or in a separate XHTML document. "
                    "Allowed values: properties or document.",
        default=None)
    version_id: Optional[int] = Field(
        description="When optimistic locking is enabled by setting the REST instance "
                    "configuration property update-policy to version-required or "
                    "version-optional, reject this request if the current version "
                    "of this document does not match the version in versionId. "
                    "Only applicable to content parts. "
                    "Ignored if optimistic locking is not enabled. "
                    "This option is equivalent to supplying a version id "
                    "through the If-Match header of a single document update.",
        default=None)
    temporal_document: Optional[str] = Field(
        description="The 'logical' document URI in the temporal collection specified "
                    "using the temporal-collection request parameter. "
                    "You can only use this parameter if the request also includes "
                    "the temporal-collection parameter.",
        default=None)
    format_: Optional[DocumentType] = Field(
        description="The content format (xml, json, text or binary)",
        alias="format",
        default=None)

    def __str__(
            self,
    ) -> str:
        """Stringify the Content-Disposition header."""
        disposition = [
            self._get_disposition(self.body_part_type),
            self._get_disposition(self.filename, "filename"),
            self._get_disposition(self.category, "category"),
            self._get_disposition(self.extension, "extension"),
            self._get_disposition(self.directory, "directory"),
            self._get_disposition(self.repair, "repair"),
            self._get_disposition(self.extract, "extract"),
            self._get_disposition(self.version_id, "versionId"),
            self._get_disposition(self.temporal_document, "temporal-document"),
            self._get_disposition(self.format_, "format"),
        ]

        return "; ".join([disp for disp in disposition if disp is not None])

    @staticmethod
    def _get_disposition(
            disp_value: str | int | Enum,
            disp: Optional[str] = None,
    ) -> Optional[str]:
        if disp_value is None:
            return None

        final_value = disp_value.value if isinstance(disp_value, Enum) else disp_value
        return final_value if disp is None else f"{disp}={final_value}"


class DocumentsBodyPart(BaseModel):
    """A class representing /v1/documents body part."""

    content_type: str = Field(
        alias="content-type",
        default=HEADER_JSON)
    content_disposition: Union[str, DocumentsContentDisposition] = Field(
        alias="content-disposition")
    content: Union[str, bytes, dict]
