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
    * StringDocument
        A Document implementation representing a single MarkLogic document.
    * BytesDocument
        A Document implementation representing a single MarkLogic document.
    * JSONDocument
        A Document implementation representing a single MarkLogic document.
    * XMLDocument
        A Document implementation representing a single MarkLogic document.
    * Metadata
        A class representing MarkLogic's document metadata.
    * Permission:
        A class representing MarkLogic's document permission.
    * Mimetype
        A class representing mime type

Examples
--------
>>> from mlclient.model import Document, DocumentType, Metadata
"""
from .data import (BytesDocument, Document, DocumentType, JSONDocument,
                   Metadata, Mimetype, Permission, StringDocument, XMLDocument)

__all__ = ["Document", "StringDocument", "BytesDocument", "JSONDocument", "XMLDocument",
           "DocumentType", "Metadata", "Mimetype", "Permission"]
