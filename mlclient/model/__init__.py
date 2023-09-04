"""The ML Model package.

It contains modules with a corresponding Python representation of MarkLogic-related
data structures:

    * data
        The ML Data module.

This package exports the following classes:

    * DocumentType
        An enumeration class representing document types.
    * Document
        A class representing a single MarkLogic document.
    * Metadata
        A class representing MarkLogic's document metadata.
    * Permission:
        A class representing MarkLogic's document permission.

Examples
--------
>>> from mlclient.model import Document, DocumentType, Metadata
"""
from .data import Document, DocumentType, Metadata, Permission

__all__ = ["Document", "DocumentType", "Metadata", "Permission"]
