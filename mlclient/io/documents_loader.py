"""The ML Documents Loader module.

It exports a class parsing files into Documents:
    * DocumentsLoader
        A class parsing files into Documents.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from pathlib import Path

from mlclient.mimetypes import Mimetypes
from mlclient.models import Document, Metadata

logger = logging.getLogger(__name__)


class DocumentsLoader:
    """A class parsing files into Documents."""

    _JSON_METADATA_SUFFIX = ".metadata.json"
    _XML_METADATA_SUFFIX = ".metadata.xml"
    _METADATA_SUFFIXES = (_JSON_METADATA_SUFFIX, _XML_METADATA_SUFFIX)

    @classmethod
    def load(
        cls,
        path: str,
        uri_prefix: str = "",
    ) -> Generator[Document]:
        """Load documents from files under a path.

        When the path points to a file - yields a single Document with URI set to
        the file name. Otherwise, yields documents with URIs without the input path
        at the beginning. Both options can be customized with the uri_prefix
        parameter.
        File bytes are stored as-is on the resulting Document; structural parsing
        (XML, JSON) happens lazily on first ``.content`` access.
        Metadata is identified for a file at the same level with .metadata.json or
        .metadata.xml suffix.

        Parameters
        ----------
        path : str
            A path to a directory or a single file.
        uri_prefix : str, default ""
            URIs prefix to apply

        Returns
        -------
        Generator[Document]
            A generator of Document instances
        """
        if Path(path).is_file():
            file_path = path
            path = Path(path)
            uri = file_path.replace(str(path.parent), uri_prefix)
            yield cls.load_document(file_path, uri)
        else:
            logger.debug("Loading documents from [%s] directory", path)
            for dir_path, _, file_names in os.walk(path):
                for file_name in file_names:
                    if file_name.endswith(cls._METADATA_SUFFIXES):
                        continue

                    file_path = str(Path(dir_path) / file_name)
                    uri = file_path.replace(path, uri_prefix)
                    yield cls.load_document(file_path, uri)

    @classmethod
    def load_document(
        cls,
        path: str,
        uri: str | None = None,
    ) -> Document:
        """Load a document from a file.

        By default, returns a Document without URI. It can be customized with
        the uri parameter.
        File bytes are stored as-is on the resulting Document; structural parsing
        (XML, JSON) happens lazily on first ``.content`` access.
        Metadata is identified for a file at the same level with .metadata.json or
        .metadata.xml suffix.

        Parameters
        ----------
        path : str
            A file path
        uri : str | None, default None
            URI to set for a document.

        Returns
        -------
        Document
            A Document instance
        """
        doc_type = Mimetypes.get_doc_type(path)
        with Path(path).open("rb") as file:
            content = file.read()
        metadata = cls._load_metadata(path)

        return Document.create(
            content=content,
            doc_type=doc_type,
            uri=uri,
            metadata=metadata,
        )

    @classmethod
    def _load_metadata(
        cls,
        path: str,
    ) -> Metadata | None:
        """Load document's metadata.

        It looks for a file with the same name and .metadata.json or .metadata.xml
        suffix and returns a Metadata instance with the raw payload preserved -
        parsing is deferred until a field accessor is called.

        Parameters
        ----------
        path : str
            A document path

        Returns
        -------
        Metadata | None
            Document's metadata or None
        """
        metadata_paths = [
            Path(path).with_suffix(cls._JSON_METADATA_SUFFIX),
            Path(path).with_suffix(cls._XML_METADATA_SUFFIX),
        ]
        metadata_file_path = next(
            (str(path) for path in metadata_paths if path.is_file()),
            None,
        )
        if not metadata_file_path:
            return None

        logger.fine("Document [%s] loaded with metadata [%s]", path, metadata_file_path)
        with Path(metadata_file_path).open("rb") as metadata_file:
            return Metadata(raw=metadata_file.read())
