"""Backward-compatible alias for document structures.

The public structures API lives in ``mlclient.structures``. This module keeps
the historical ``mlclient.model`` import path working for existing users and
for documentation examples that still reference it.
"""

from mlclient.structures import (
    BinaryDocument,
    Document,
    DocumentFactory,
    DocumentType,
    JSONDocument,
    Metadata,
    MetadataDocument,
    MetadataFactory,
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
    "DocumentFactory",
    "DocumentType",
    "JSONDocument",
    "Metadata",
    "MetadataDocument",
    "MetadataFactory",
    "Mimetype",
    "Permission",
    "RawDocument",
    "RawStringDocument",
    "TextDocument",
    "XMLDocument",
]
