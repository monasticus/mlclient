"""The ML Model package.

It contains modules with a corresponding Python representation of MarkLogic-related
data structures. Exports the following packages:

    * calls
        The ML Calls Model package.

This package exports the following modules:

    * data
        The ML Data module.

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
    * Metadata
        A class representing MarkLogic's document metadata.
    * Permission:
        A class representing MarkLogic's document permission.

Examples
--------
>>> from mlclient.model import Document, DocumentType, Metadata
"""
from .data import (BinaryDocument, Document, DocumentType, JSONDocument,
                   Metadata, Permission, RawDocument, RawStringDocument,
                   TextDocument, XMLDocument)

__all__ = ["Document", "RawDocument", "RawStringDocument",
           "XMLDocument", "JSONDocument", "TextDocument", "BinaryDocument",
           "DocumentType", "Metadata", "Permission"]
