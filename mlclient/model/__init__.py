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
    * Metadata
        A class representing MarkLogic's document metadata.
    * Permission:
        A class representing MarkLogic's document permission.

Examples
--------
>>> from mlclient.model import Document, DocumentType, Metadata
"""
from .data import Document, DocumentType, Metadata, Permission, StringDocument

__all__ = ["Document", "DocumentType", "Metadata", "Permission", "StringDocument"]
