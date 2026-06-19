"""The ML Models types module.

It exports the following classes:
    * DocumentType
        An enumeration class representing document types.
    * Mimetype
        A class representing a mime type.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(Enum):
    """An enumeration class representing document types."""

    XML: str = "xml"
    JSON: str = "json"
    BINARY: str = "binary"
    TEXT: str = "text"


class Mimetype(BaseModel):
    """A class representing a mime type."""

    mime_type: str = Field(alias="mime-type")
    extensions: list[str]
    document_type: DocumentType = Field(alias="doc-type")
