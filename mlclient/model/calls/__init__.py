"""The ML Calls Model package.

It contains modules with a corresponding Python representation of
ML calls-specific data structures:

    * documents
        The Documents Call Model module.

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

Examples
--------
>>> from mlclient.model.calls import DocumentsBodyPart
"""
from .documents import (DocumentsBodyPartType, DocumentsBodyPart,
                        DocumentsContentDisposition, Extract, Repair)

__all__ = ["DocumentsBodyPartType", "DocumentsBodyPart",
           "DocumentsContentDisposition", "Extract", "Repair"]
