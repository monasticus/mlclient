"""The ML Documents Writer module.

It exports a class serializing Documents into files:
    * DocumentsWriter
        A class serializing Documents into files.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

import aiofiles

from mlclient.models import Document, Metadata

logger = logging.getLogger(__name__)


class DocumentsWriter:
    """A class serializing Documents into files."""

    _JSON_METADATA_SUFFIX = ".metadata.json"
    _XML_METADATA_SUFFIX = ".metadata.xml"

    @classmethod
    async def write(
        cls,
        documents: Iterable[Document],
        output_path: str,
    ) -> None:
        """Write documents to files under a path.

        Each document is written to ``output_path`` joined with its URI. When a
        document carries metadata, a ``.metadata.json`` or ``.metadata.xml``
        sidecar is written alongside it - the suffix matches the format of the
        metadata payload so a round-trip through DocumentsLoader preserves it.

        Parameters
        ----------
        documents : Iterable[Document]
            The documents to write.
        output_path : str
            A path to the output directory.
        """
        for document in documents:
            await cls.write_document(document, output_path)

    @classmethod
    async def write_document(
        cls,
        document: Document,
        output_path: str,
    ) -> None:
        """Write a single document to a file under a path.

        For content-bearing documents writes the content body and, when
        present, a metadata sidecar. For metadata-only documents
        (``MetadataDocument``, whose ``content_bytes`` is None) writes the
        sidecar without a content file.

        Parameters
        ----------
        document : Document
            The document to write.
        output_path : str
            A path to the output directory.
        """
        doc_path = Path(output_path) / document.uri[1:]
        doc_path.parent.mkdir(parents=True, exist_ok=True)

        if document.content_bytes is not None:
            logger.fine("Writing data into file [%s]", doc_path)
            async with aiofiles.open(doc_path, mode="wb") as file:
                await file.write(document.content_bytes)

        if document.metadata is not None:
            await cls._write_metadata(document.metadata, doc_path)

    @classmethod
    async def _write_metadata(
        cls,
        metadata: Metadata,
        doc_path: Path,
    ) -> None:
        """Write a document's metadata sidecar next to its content file.

        Prefers the raw payload when available to avoid a re-serialization
        round-trip, picking the sidecar suffix from its format. Falls back to a
        JSON serialization when the metadata was built from fields or has
        already been parsed.
        """
        raw = metadata.raw()
        if raw is not None:
            payload = raw if isinstance(raw, bytes) else raw.encode("utf-8")
            suffix = (
                cls._XML_METADATA_SUFFIX
                if cls._is_xml(raw)
                else cls._JSON_METADATA_SUFFIX
            )
        else:
            payload = metadata.to_json_string().encode("utf-8")
            suffix = cls._JSON_METADATA_SUFFIX

        metadata_path = doc_path.with_suffix(suffix)
        logger.fine("Writing metadata into file [%s]", metadata_path)
        async with aiofiles.open(metadata_path, mode="wb") as file:
            await file.write(payload)

    @classmethod
    def _is_xml(
        cls,
        raw: bytes | str,
    ) -> bool:
        """Tell whether a raw metadata payload is XML rather than JSON."""
        source = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return source.lstrip().startswith("<")
