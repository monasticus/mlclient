"""The ML Calls Structures package.

It contains modules with a corresponding Python representation of
ML calls-specific data structures:

    * documents
        The Documents Call Structures module.

This package exports the following classes:

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
    * ContentDispositionSerializer
        A Content-Disposition header serializer.

Examples
--------
>>> from mlclient.structures.calls import DocumentsBodyPart
"""
from .documents import (
    Category,
    ContentDispositionSerializer,
    DocumentsBodyPart,
    DocumentsBodyPartType,
    DocumentsContentDisposition,
    Extract,
    Repair,
)

__all__ = [
    "DocumentsBodyPart",
    "DocumentsBodyPartType",
    "DocumentsContentDisposition",
    "Category",
    "Extract",
    "Repair",
    "ContentDispositionSerializer",
]
