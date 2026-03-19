"""The ML Structures package.

It contains modules with a corresponding Python representation of MarkLogic-related
data structures:

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
    * RawDocument
        A Document implementation representing a single MarkLogic document.
    * RawStringDocument
        A Document implementation representing a single MarkLogic document.
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
>>> from mlclient.structures import Document, DocumentType, Metadata
"""

from .documents import (
    BinaryDocument,
    Document,
    DocumentType,
    JSONDocument,
    Metadata,
    MetadataDocument,
    Mimetype,
    Permission,
    RawDocument,
    RawStringDocument,
    TextDocument,
    XMLDocument,
)

__all__ = [
    "BinaryDocument",
    "Document",
    "DocumentType",
    "JSONDocument",
    "Metadata",
    "MetadataDocument",
    "Mimetype",
    "Permission",
    "RawDocument",
    "RawStringDocument",
    "TextDocument",
    "XMLDocument",
]
