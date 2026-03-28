"""The ML HTTP Models package.

It contains modules with a corresponding Python representation of
HTTP-specific data models:

    * documents
        The Documents HTTP Models module.

This package exports the following classes:

    * DocumentsBodyPart
        A class representing /v1/documents body part.
    * DocumentsDisposition
        A class representing /v1/documents body part Content-Disposition header.
    * DocumentsBodyPartType
        An enumeration class representing /v1/documents body part types.
    * Repair
        An enumeration class representing repair levels.
    * Extract
        An enumeration class representing metadata extract types.
    * Category
        An enumeration class representing data categories.

Examples
--------
>>> from mlclient.models.http import DocumentsBodyPart
>>> from mlclient.models.http.documents import BodyPart  # unprefixed
"""

from .documents import BodyPart as DocumentsBodyPart
from .documents import BodyPartType as DocumentsBodyPartType
from .documents import Category
from .documents import Disposition as DocumentsDisposition
from .documents import Extract, Repair

__all__ = [
    "Category",
    "DocumentsBodyPart",
    "DocumentsBodyPartType",
    "DocumentsDisposition",
    "Extract",
    "Repair",
]
