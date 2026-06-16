"""The ML Models package.

It contains modules with a corresponding Python representation of MarkLogic-related
data models:

    * documents
        The ML Documents module.

This package exports the following classes:

    * DocumentType
        An enumeration class representing document types.
    * Document
        A class representing a single MarkLogic document.
    * JSONDocument
        A Document implementation representing a single MarkLogic JSON document.
    * XMLDocument
        A Document implementation representing a single MarkLogic XML document.
    * TextDocument
        A Document implementation representing a single MarkLogic TEXT document.
    * BinaryDocument
        A Document implementation representing a single MarkLogic BINARY document.
    * MetadataDocument
        A Document implementation representing a single MarkLogic document's metadata.
    * Metadata
        A class representing MarkLogic's document metadata.
    * Permission:
        A class representing MarkLogic's document permission.
    * Mimetype
        A class representing mime type

Examples
--------
>>> from mlclient.models import Document, DocumentType, Metadata
"""

from .documents import (
    BinaryDocument,
    Document,
    JSONDocument,
    Metadata,
    MetadataDocument,
    Permission,
    TextDocument,
    XMLDocument,
)
from .types import DocumentType, Mimetype

__all__ = [
    "BinaryDocument",
    "Document",
    "DocumentType",
    "JSONDocument",
    "Metadata",
    "MetadataDocument",
    "Mimetype",
    "Permission",
    "TextDocument",
    "XMLDocument",
]
