"""The ML Data module.

It exports the following classes:
    * DocumentType
        An enumeration class representing document types.
    * Document
        An abstract class representing a single MarkLogic document.
    * JSONDocument
        A Document implementation representing a single MarkLogic JSON document.
    * XMLDocument
        A Document implementation representing a single MarkLogic XML document.
    * TextDocument
        A Document implementation representing a single MarkLogic TEXT document.
    * BinaryDocument
        A Document implementation representing a single MarkLogic BINARY document.
    * MetadataDocument
        A Document implementation representing a single MarkLogic document's metadata.
    * Metadata
        A class representing MarkLogic's document metadata.
    * Permission:
        A class representing MarkLogic's document permission.
    * Mimetype
        A class representing mime type.
"""

from __future__ import annotations

import copy
import json
import logging
import re
import xml.etree.ElementTree as ElemTree
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, TextIO
from xml.dom import minidom

import xmltodict

from mlclient.exceptions import InvalidMetadataError
from mlclient.mimetypes import Mimetypes
from mlclient.models.types import DocumentType

logger = logging.getLogger(__name__)


class Document(metaclass=ABCMeta):
    """An abstract class representing a single MarkLogic document."""

    def __init__(
        self,
        uri: str | None = None,
        doc_type: DocumentType | None = DocumentType.XML,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ):
        """Initialize Document instance.

        Parameters
        ----------
        uri : str
            A document URI
        doc_type : DocumentType | None
            A document type
        metadata : Metadata
            A document metadata
        temporal_collection : str | None
            The temporal collection
        """
        self._uri = self._get_non_blank_uri(uri)
        self._doc_type = doc_type
        if isinstance(metadata, (bytes, str)):
            metadata = Metadata(raw=metadata)
        self._metadata = metadata
        self._temporal_collection = temporal_collection

    @classmethod
    def __subclasshook__(
        cls,
        subclass: Document,
    ):
        """Verify if a subclass implements all abstract methods.

        Parameters
        ----------
        subclass : Document
            A Document subclass

        Returns
        -------
        bool
            True if the subclass includes the content property
        """
        return (
            "content" in subclass.__dict__
            and not callable(subclass.content)
            and "content_bytes" in subclass.__dict__
            and not callable(subclass.content_bytes)
            and "content_string" in subclass.__dict__
            and not callable(subclass.content_string)
        )

    @classmethod
    def create(
        cls,
        uri: str | None = None,
        content: ElemTree.Element | dict | str | bytes | None = None,
        *,
        doc_type: DocumentType | str | None = None,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ) -> Document:
        """Instantiate a typed Document, inferring type from content and URI.

        The factory methods (``create``, ``xml``, ``json``, ``text``,
        ``binary``, ``metadata_update``) take ``uri`` first - they read as
        "create a document at this URI with this content". The concrete
        constructors (``XMLDocument`` etc.) take ``content`` first, since
        content is their only required argument and a URI-less document is
        valid (e.g. one loaded from a file, with its URI assigned on write).

        Type inference order:
        1. Explicit ``doc_type`` parameter.
        2. ``ElemTree.Element`` content -> XML.
        3. ``dict`` content -> JSON.
        4. ``str`` or ``bytes`` content + ``uri`` -> ``Mimetypes.get_doc_type(uri)``
           (fallback: BINARY when the extension is unrecognised).
        5. ``str`` content, no URI -> TEXT.
        6. ``bytes`` content, no URI -> BINARY.

        Parameters
        ----------
        uri : str | None, default None
            A document URI.
        content : ElemTree.Element | dict | str | bytes | None, default None
            A document content.
        doc_type : DocumentType | str | None, default None
            A document type override.
        metadata : Metadata | bytes | str | None, default None
            A document metadata.
        temporal_collection : str | None, default None
            The temporal collection.

        Returns
        -------
        Document
            A typed Document subclass instance.

        Raises
        ------
        TypeError
            If both ``content`` and ``doc_type`` are None (use
            ``Document.metadata_update()`` for metadata-only updates).
        """
        if isinstance(doc_type, str):
            doc_type = DocumentType(doc_type)

        if content is None and doc_type is None:
            msg = (
                "Cannot infer document type: provide content, doc_type, "
                "or use Document.metadata_update() for metadata-only updates"
            )
            raise TypeError(msg)

        resolved_type = _resolve_doc_type(content, doc_type, uri)
        impl = _TYPED_IMPLS[resolved_type]
        return impl(
            content=content,
            uri=uri,
            metadata=metadata,
            temporal_collection=temporal_collection,
        )

    @classmethod
    def xml(
        cls,
        uri: str | None = None,
        content: ElemTree.Element | str | bytes | None = None,
        *,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ) -> XMLDocument:
        """Instantiate an XMLDocument.

        Accepts ``ElemTree.Element``, ``str``, or ``bytes`` content.
        String and bytes are stored as-is; parsing to ElementTree is deferred
        to the first ``.content`` access.

        Parameters
        ----------
        uri : str | None, default None
            A document URI.
        content : ElemTree.Element | str | bytes
            XML content. Required; ``None`` raises ``TypeError``.
        metadata : Metadata | bytes | str | None, default None
            A document metadata.
        temporal_collection : str | None, default None
            The temporal collection.

        Returns
        -------
        XMLDocument
        """
        return XMLDocument(
            content=content,
            uri=uri,
            metadata=metadata,
            temporal_collection=temporal_collection,
        )

    @classmethod
    def json(
        cls,
        uri: str | None = None,
        content: dict | str | bytes | None = None,
        *,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ) -> JSONDocument:
        """Instantiate a JSONDocument.

        Accepts ``dict``, ``str``, or ``bytes`` content.
        String and bytes are stored as-is; parsing to dict is deferred to the
        first ``.content`` access.

        Parameters
        ----------
        uri : str | None, default None
            A document URI.
        content : dict | str | bytes
            JSON content. Required; ``None`` raises ``TypeError``.
        metadata : Metadata | bytes | str | None, default None
            A document metadata.
        temporal_collection : str | None, default None
            The temporal collection.

        Returns
        -------
        JSONDocument
        """
        return JSONDocument(
            content=content,
            uri=uri,
            metadata=metadata,
            temporal_collection=temporal_collection,
        )

    @classmethod
    def text(
        cls,
        uri: str | None = None,
        content: str | bytes | None = None,
        *,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ) -> TextDocument:
        """Instantiate a TextDocument.

        Parameters
        ----------
        uri : str | None, default None
            A document URI.
        content : str | bytes
            Text content. Required; ``None`` raises ``TypeError``.
        metadata : Metadata | bytes | str | None, default None
            A document metadata.
        temporal_collection : str | None, default None
            The temporal collection.

        Returns
        -------
        TextDocument
        """
        return TextDocument(
            content=content,
            uri=uri,
            metadata=metadata,
            temporal_collection=temporal_collection,
        )

    @classmethod
    def binary(
        cls,
        uri: str | None = None,
        content: bytes | None = None,
        *,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ) -> BinaryDocument:
        """Instantiate a BinaryDocument.

        Parameters
        ----------
        uri : str | None, default None
            A document URI.
        content : bytes
            Binary content. Required; ``None`` raises ``TypeError``.
        metadata : Metadata | bytes | str | None, default None
            A document metadata.
        temporal_collection : str | None, default None
            The temporal collection.

        Returns
        -------
        BinaryDocument
        """
        return BinaryDocument(
            content=content,
            uri=uri,
            metadata=metadata,
            temporal_collection=temporal_collection,
        )

    @classmethod
    def metadata_update(
        cls,
        uri: str,
        metadata: Metadata | bytes | str,
        *,
        temporal_collection: str | None = None,
    ) -> MetadataDocument:
        """Instantiate a MetadataDocument for a metadata-only update.

        Updates the metadata of an existing MarkLogic document without
        touching its content body.

        Parameters
        ----------
        uri : str
            A document URI.
        metadata : Metadata | bytes | str
            Document metadata to apply.
        temporal_collection : str | None, default None
            The temporal collection.

        Returns
        -------
        MetadataDocument

        Raises
        ------
        TypeError
            If uri is blank or metadata is None.
        """
        if not uri or (isinstance(uri, str) and not uri.strip()):
            msg = "uri is required for Document.metadata_update()"
            raise TypeError(msg)
        if metadata is None:
            msg = "metadata is required for Document.metadata_update()"
            raise TypeError(msg)
        return MetadataDocument(
            uri=uri,
            metadata=metadata,
            temporal_collection=temporal_collection,
        )

    @property
    @abstractmethod
    def content(
        self,
    ) -> Any:
        """A document content.

        Typed content-bearing implementations narrow this to a non-``None``
        return type (``ElemTree.ElementTree``, ``dict``, ``str``, ``bytes``).
        ``MetadataDocument`` carries no content body and returns ``None``.

        Returns
        -------
        Any
            A document's content, or ``None`` for metadata-only documents.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def content_bytes(
        self,
    ) -> bytes | None:
        """A document content bytes.

        Typed content-bearing documents (``XMLDocument``, ``JSONDocument``,
        ``TextDocument``, ``BinaryDocument``) always return ``bytes`` and
        narrow this return type accordingly. ``MetadataDocument`` carries no
        content body and returns ``None``; callers that operate on a generic
        ``Document`` must handle that case before writing to a bytes sink.

        Returns
        -------
        bytes | None
            A document's content bytes, or ``None`` for metadata-only
            documents.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def content_string(
        self,
    ) -> str | None:
        """A document content as a string.

        ``XMLDocument``, ``JSONDocument`` and ``TextDocument`` always return
        ``str`` and narrow this return type accordingly. ``BinaryDocument``
        and ``MetadataDocument`` return ``None`` - binary content has no
        meaningful string representation and metadata-only documents carry
        no content body.

        Returns
        -------
        str | None
            A document's content as a string, or ``None`` for binary or
            metadata-only documents.
        """
        raise NotImplementedError

    @property
    def uri(
        self,
    ) -> str:
        """A document URI."""
        return self._uri

    @property
    def doc_type(
        self,
    ) -> DocumentType | None:
        """A document type."""
        return self._doc_type

    @property
    def metadata(
        self,
    ) -> Metadata | bytes | str:
        """A document metadata."""
        return copy.copy(self._metadata)

    @property
    def temporal_collection(
        self,
    ) -> str | None:
        """The temporal collection."""
        return self._temporal_collection

    @staticmethod
    def _get_non_blank_uri(
        uri: str,
    ) -> str | None:
        """Return URI or None when blank."""
        return uri if uri is not None and not re.search("^\\s*$", uri) else None


class JSONDocument(Document):
    """A Document implementation representing a single MarkLogic JSON document.

    Accepts ``dict``, ``str``, or ``bytes`` content. String and bytes are stored
    as-is; parsing to ``dict`` is deferred to the first ``.content`` access.
    """

    def __init__(
        self,
        content: dict | str | bytes,
        uri: str | None = None,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ):
        if content is None:
            msg = (
                "JSONDocument requires content; "
                "use Document.metadata_update() for metadata-only updates"
            )
            raise TypeError(msg)
        super().__init__(uri, DocumentType.JSON, metadata, temporal_collection)
        self._parsed: dict | None = content if isinstance(content, dict) else None
        self._content_bytes: bytes | None = (
            content if isinstance(content, bytes) else None
        )
        self._content_string: str | None = content if isinstance(content, str) else None

    @property
    def content(self) -> dict:
        """A parsed dict representation of JSON content.

        Parsing from the raw string/bytes form is deferred to the first access
        and cached for subsequent calls.

        Returns
        -------
        dict
            The parsed JSON content as a dictionary.
        """
        if self._parsed is None:
            raw = (
                self._content_bytes
                if self._content_bytes is not None
                else self._content_string
            )
            self._parsed = json.loads(raw)
        return self._parsed

    @property
    def content_bytes(self) -> bytes:
        """A UTF-8 encoded representation of the JSON content.

        Computed once on first access and cached for subsequent calls.

        Returns
        -------
        bytes
            The content encoded as UTF-8 bytes.
        """
        if self._content_bytes is None:
            if self._content_string is not None:
                self._content_bytes = self._content_string.encode("utf-8")
            else:
                self._content_bytes = json.dumps(self._parsed).encode("utf-8")
        return self._content_bytes

    @property
    def content_string(self) -> str:
        """A string representation of the JSON content.

        Computed once on first access and cached for subsequent calls.

        Returns
        -------
        str
            The content as a string.
        """
        if self._content_string is None:
            if self._content_bytes is not None:
                self._content_string = self._content_bytes.decode("utf-8")
            else:
                self._content_string = json.dumps(self._parsed)
        return self._content_string

    def invalidate(self) -> JSONDocument:
        """Drop cached bytes/string serializations of the parsed dict.

        Use this when the parsed ``.content`` has been mutated externally so
        that subsequent ``.content_bytes`` / ``.content_string`` calls
        re-serialize from the parsed form instead of returning stale cached
        output. Has no effect when the document has not been parsed yet.

        Returns
        -------
        JSONDocument
            ``self``, so the call can be chained directly into a write.

        Examples
        --------
        >>> doc.content["name"] = "Smith"
        >>> ml.documents.write(doc.invalidate())
        """
        if self._parsed is not None:
            self._content_bytes = None
            self._content_string = None
        return self


class XMLDocument(Document):
    """A Document implementation representing a single MarkLogic XML document.

    Accepts ``ElemTree.Element``, ``str``, or ``bytes`` content.
    String and bytes are stored as-is; parsing to ``ElementTree`` is deferred
    to the first ``.content`` access.
    """

    _XML_DECL_RE: ClassVar = re.compile(r"^\s*<\?xml[^?]*\?>\s*")

    def __init__(
        self,
        content: ElemTree.ElementTree | ElemTree.Element | str | bytes,
        uri: str | None = None,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ):
        if content is None:
            msg = (
                "XMLDocument requires content; "
                "use Document.metadata_update() for metadata-only updates"
            )
            raise TypeError(msg)
        super().__init__(uri, DocumentType.XML, metadata, temporal_collection)
        if isinstance(content, ElemTree.Element):
            self._parsed: ElemTree.ElementTree | None = ElemTree.ElementTree(content)
        elif isinstance(content, ElemTree.ElementTree):
            self._parsed = content
        else:
            self._parsed = None
        self._content_bytes: bytes | None = (
            content if isinstance(content, bytes) else None
        )
        self._content_string: str | None = content if isinstance(content, str) else None

    @property
    def content(self) -> ElemTree.ElementTree:
        """A parsed ElementTree representation of the XML content.

        Parsing from the raw string/bytes form is deferred to the first access
        and cached for subsequent calls.

        Returns
        -------
        ElemTree.ElementTree
            The parsed XML content as an ElementTree.
        """
        if self._parsed is None:
            if self._content_bytes is not None:
                self._parsed = ElemTree.ElementTree(
                    ElemTree.fromstring(self._content_bytes),
                )
            else:
                source = self._XML_DECL_RE.sub("", self._content_string, count=1)
                self._parsed = ElemTree.ElementTree(ElemTree.fromstring(source))
        return self._parsed

    @property
    def content_bytes(self) -> bytes:
        """A UTF-8 encoded representation of the XML content with declaration.

        Computed once on first access and cached for subsequent calls.

        Returns
        -------
        bytes
            The content encoded as UTF-8 bytes.
        """
        if self._content_bytes is None:
            if self._content_string is not None:
                self._content_bytes = self._content_string.encode("utf-8")
            else:
                self._content_bytes = self._serialize_tree()
        return self._content_bytes

    @property
    def content_string(self) -> str:
        """A string representation of the XML content.

        Computed once on first access and cached for subsequent calls.

        Returns
        -------
        str
            The content as a string.
        """
        if self._content_string is None:
            if self._content_bytes is not None:
                self._content_string = self._content_bytes.decode("utf-8")
            else:
                self._content_string = self._serialize_tree().decode("utf-8")
        return self._content_string

    def _serialize_tree(self) -> bytes:
        """Serialize the parsed ElementTree to UTF-8 bytes with XML declaration."""
        return _normalize_xml_declaration(
            ElemTree.tostring(
                self._parsed.getroot(),
                encoding="UTF-8",
                xml_declaration=True,
            ),
        )

    def xpath(self, expr: str, **namespaces: str) -> list:
        """Run an XPath expression against the document content.

        Parameters
        ----------
        expr : str
            XPath expression.
        **namespaces : str
            Namespace prefix-to-URI mappings used in ``expr``.

        Returns
        -------
        list
            Matching elements.
        """
        return self.content.findall(expr, namespaces or None)

    def invalidate(self) -> XMLDocument:
        """Drop cached bytes/string serializations of the parsed ElementTree.

        Use this when the parsed ``.content`` has been mutated externally so
        that subsequent ``.content_bytes`` / ``.content_string`` calls
        re-serialize from the parsed form instead of returning stale cached
        output. Has no effect when the document has not been parsed yet.

        Returns
        -------
        XMLDocument
            ``self``, so the call can be chained directly into a write.

        Examples
        --------
        >>> doc.content.find("name").text = "Smith"
        >>> ml.documents.write(doc.invalidate())
        """
        if self._parsed is not None:
            self._content_bytes = None
            self._content_string = None
        return self


class TextDocument(Document):
    """A Document implementation representing a single MarkLogic TEXT document.

    This implementation stores content in a string format.
    """

    def __init__(
        self,
        content: str | bytes,
        uri: str | None = None,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ):
        if content is None:
            msg = (
                "TextDocument requires content; "
                "use Document.metadata_update() for metadata-only updates"
            )
            raise TypeError(msg)
        super().__init__(uri, DocumentType.TEXT, metadata, temporal_collection)
        self._content_string: str | None = content if isinstance(content, str) else None
        self._content_bytes: bytes | None = (
            content if isinstance(content, bytes) else None
        )

    @property
    def content(self) -> str:
        """A document content.

        Returns
        -------
        str
            The text content.
        """
        return self.content_string

    @property
    def content_bytes(self) -> bytes:
        """A document content as bytes.

        Returns
        -------
        bytes
            The text content encoded as UTF-8.
        """
        if self._content_bytes is None:
            self._content_bytes = self._content_string.encode("utf-8")
        return self._content_bytes

    @property
    def content_string(self) -> str:
        """A document content as a string.

        Returns
        -------
        str
            The text content.
        """
        if self._content_string is None:
            self._content_string = self._content_bytes.decode("utf-8")
        return self._content_string


class BinaryDocument(Document):
    """A Document implementation representing a single MarkLogic BINARY document.

    This implementation stores content in bytes format.
    """

    def __init__(
        self,
        content: bytes,
        uri: str | None = None,
        metadata: Metadata | bytes | str | None = None,
        temporal_collection: str | None = None,
    ):
        if content is None:
            msg = (
                "BinaryDocument requires content; "
                "use Document.metadata_update() for metadata-only updates"
            )
            raise TypeError(msg)
        super().__init__(uri, DocumentType.BINARY, metadata, temporal_collection)
        self._content_bytes = content

    @property
    def content(self) -> bytes:
        """A document content.

        Returns
        -------
        bytes
            The binary content.
        """
        return self._content_bytes

    @property
    def content_bytes(self) -> bytes:
        """A document content as bytes.

        Returns
        -------
        bytes
            The binary content.
        """
        return self._content_bytes

    @property
    def content_string(self) -> None:
        """A document content as a string.

        Returns
        -------
        None
            Always None; binary content has no meaningful string
            representation.
        """
        return None


class MetadataDocument(Document):
    """A Document implementation for metadata-only updates.

    Does not store document content. Use ``Document.metadata_update()`` to
    create instances rather than calling the constructor directly.
    """

    def __init__(
        self,
        uri: str,
        metadata: Metadata | bytes | str,
        temporal_collection: str | None = None,
    ):
        super().__init__(
            uri,
            doc_type=None,
            metadata=metadata,
            temporal_collection=temporal_collection,
        )

    @property
    def content(self) -> None:
        """A document content.

        Returns
        -------
        None
            Always None; metadata-only documents have no content.
        """
        return None

    @property
    def content_bytes(self) -> None:
        """A document content as bytes.

        Returns
        -------
        None
            Always None; metadata-only documents have no content.
        """
        return None

    @property
    def content_string(self) -> None:
        """A document content as a string.

        Returns
        -------
        None
            Always None; metadata-only documents have no content.
        """
        return None


_TYPED_IMPLS: dict[DocumentType, type] = {
    DocumentType.XML: XMLDocument,
    DocumentType.JSON: JSONDocument,
    DocumentType.TEXT: TextDocument,
    DocumentType.BINARY: BinaryDocument,
}


def _resolve_doc_type(
    content: ElemTree.Element | dict | str | bytes | None,
    doc_type: DocumentType | None,
    uri: str | None,
) -> DocumentType:
    """Resolve the document type from an explicit type, content Python type, and URI.

    Resolution order:
    1. Explicit ``doc_type``.
    2. ``ElemTree.Element`` -> XML.
    3. ``dict`` -> JSON.
    4. ``str``/``bytes`` + ``uri`` -> ``Mimetypes.get_doc_type(uri)``.
    5. ``str`` + no URI -> TEXT.
    6. ``bytes`` + no URI -> BINARY.
    """
    if doc_type is not None:
        return doc_type
    if isinstance(content, ElemTree.Element):
        return DocumentType.XML
    if isinstance(content, dict):
        return DocumentType.JSON
    if isinstance(content, (str, bytes)):
        if uri:
            return Mimetypes.get_doc_type(uri)
        return DocumentType.TEXT if isinstance(content, str) else DocumentType.BINARY
    msg = "Unsupported document type! Document types are: XML, JSON, TEXT, BINARY!"
    raise NotImplementedError(msg)


_XML_DECL_RE = re.compile(
    rb"^\s*<\?xml\s+version=['\"][^'\"]*['\"]\s+encoding=['\"][^'\"]*['\"]\s*\?>",
)
_XML_DECL_CANONICAL = b'<?xml version="1.0" encoding="UTF-8"?>'


def _normalize_xml_declaration(serialized: bytes) -> bytes:
    """Rewrite the leading XML declaration to a canonical form.

    Produces ``<?xml version="1.0" encoding="UTF-8"?>`` regardless of the
    quote style and encoding case emitted by ElementTree (single quotes,
    lowercase ``utf-8``) or minidom (double quotes, lowercase ``utf-8``).
    """
    return _XML_DECL_RE.sub(_XML_DECL_CANONICAL, serialized, count=1)


class Metadata:
    """A class representing MarkLogic's document metadata."""

    _COLLECTIONS_KEY: str = "collections"
    _PERMISSIONS_KEY: str = "permissions"
    _PROPERTIES_KEY: str = "properties"
    _QUALITY_KEY: str = "quality"
    _METADATA_VALUES_KEY: str = "metadataValues"

    _METADATA_TAG: str = "rapi:metadata"
    _COLLECTIONS_TAG: str = "rapi:collections"
    _COLLECTION_TAG: str = "rapi:collection"
    _PERMISSIONS_TAG: str = "rapi:permissions"
    _PERMISSION_TAG: str = "rapi:permission"
    _ROLE_NAME_TAG: str = "rapi:role-name"
    _CAPABILITY_TAG: str = "rapi:capability"
    _PROPERTIES_TAG: str = "prop:properties"
    _QUALITY_TAG: str = "rapi:quality"
    _METADATA_VALUES_TAG: str = "rapi:metadata-values"
    _METADATA_VALUE_TAG: str = "rapi:metadata-value"
    _KEY_ATTR: str = "key"

    _RAPI_NS_PREFIX: str = "xmlns:rapi"
    _PROP_NS_PREFIX: str = "xmlns:prop"
    _RAPI_NS_URI: str = "http://marklogic.com/rest-api"
    _PROP_NS_URI: str = "http://marklogic.com/xdmp/property"

    _XML_FILE_MAPPINGS: ClassVar[dict] = {
        "collections": "collection",
        "permissions": "permission",
        "metadata-values": "metadata-value",
    }
    _VALID_XML_CHILDREN: ClassVar[set] = {
        "collections",
        "permissions",
        "properties",
        "quality",
        "metadata-values",
    }

    @classmethod
    def from_file(
        cls,
        file_path: str,
    ) -> Metadata:
        """Initialize a Metadata instance from a file.

        Parameters
        ----------
        file_path : str
            A metadata file path

        Returns
        -------
        Metadata
            A Metadata instance
        """
        file_path = Path(file_path)
        with file_path.open() as file:
            if file_path.suffix == ".json":
                return cls._from_json_file(file)
            return cls._from_xml_file(file)

    @classmethod
    def _from_json_file(
        cls,
        file: TextIO,
    ) -> Metadata:
        """Initialize a Metadata instance from a JSON file."""
        return Metadata(**cls._parse_json(file.read()))

    @classmethod
    def _from_xml_file(
        cls,
        file: TextIO,
    ) -> Metadata:
        """Initialize a Metadata instance from an XML file."""
        return Metadata(**cls._parse_xml(file.read()))

    @classmethod
    def _parse_json(
        cls,
        content: str,
    ) -> dict:
        """Parse a JSON metadata payload to Metadata constructor kwargs."""
        raw_metadata = json.loads(content)
        if "permissions" in raw_metadata:
            permissions = []
            for permission in raw_metadata["permissions"]:
                role_name = permission["role-name"]
                capabilities = permission["capabilities"]
                permissions.append(Permission(role_name, set(capabilities)))
            raw_metadata["permissions"] = permissions
        if "metadataValues" in raw_metadata:
            raw_metadata["metadata_values"] = raw_metadata["metadataValues"]
            del raw_metadata["metadataValues"]
        return raw_metadata

    @classmethod
    def _parse_xml(
        cls,
        content: str,
    ) -> dict:
        """Parse an XML metadata payload to Metadata constructor kwargs.

        Empty XML elements (``<rapi:collections/>``, ``<rapi:permissions/>``
        etc.) are normal in MarkLogic responses for documents that have no
        values for a category. ``xmltodict`` represents them as ``None``;
        treat them as absent so ``Metadata.__init__`` defaults take over.
        """
        cls._validate_xml_metadata(content)
        parsed = xmltodict.parse(
            content,
            process_namespaces=True,
            namespaces={
                cls._RAPI_NS_URI: None,
                cls._PROP_NS_URI: None,
            },
        )
        metadata_node = parsed["metadata"] or {}
        raw_metadata = {k: v for k, v in metadata_node.items() if v is not None}
        for items, item in cls._XML_FILE_MAPPINGS.items():
            if items in raw_metadata:
                values = raw_metadata[items][item]
                if not isinstance(values, list):
                    values = [values]
                raw_metadata[items] = values
        if "permissions" in raw_metadata:
            permissions = []
            for permission in raw_metadata["permissions"]:
                role_name = permission["role-name"]
                capability = permission["capability"]
                existing_perm = next(
                    (p for p in permissions if p.role_name() == role_name),
                    None,
                )
                if existing_perm is None:
                    permissions.append(Permission(role_name, {capability}))
                else:
                    existing_perm.add_capability(capability)
            raw_metadata["permissions"] = permissions
        if "metadata-values" in raw_metadata:
            metadata_values = {}
            for metadata_value in raw_metadata["metadata-values"]:
                key = metadata_value["@key"]
                value = metadata_value["#text"]
                metadata_values[key] = value
            raw_metadata["metadata_values"] = metadata_values
            del raw_metadata["metadata-values"]
        if "quality" in raw_metadata:
            raw_metadata["quality"] = int(raw_metadata["quality"])
        return raw_metadata

    @classmethod
    def _validate_xml_metadata(
        cls,
        content: str,
    ) -> None:
        """Validate XML metadata structure before parsing."""
        root = ElemTree.fromstring(content)
        expected_root = f"{{{cls._RAPI_NS_URI}}}metadata"
        if root.tag != expected_root:
            msg = f"Unexpected root element [{root.tag}]; expected [{expected_root}]"
            raise InvalidMetadataError(msg)
        valid_namespaces = {cls._RAPI_NS_URI, cls._PROP_NS_URI}
        for child in root:
            ns = child.tag.split("}")[0].lstrip("{") if "}" in child.tag else None
            if ns not in valid_namespaces:
                msg = f"Unexpected element [{child.tag}] in metadata"
                raise InvalidMetadataError(msg)
            local_name = child.tag.split("}")[1] if "}" in child.tag else child.tag
            if ns == cls._RAPI_NS_URI and local_name not in cls._VALID_XML_CHILDREN:
                msg = f"Unexpected element [{child.tag}] in metadata"
                raise InvalidMetadataError(msg)

    def __init__(
        self,
        collections: list | None = None,
        permissions: list | None = None,
        properties: dict | None = None,
        quality: int = 0,
        metadata_values: dict | None = None,
        *,
        raw: bytes | str | None = None,
    ):
        """Initialize Metadata instance.

        Parameters
        ----------
        collections : list | None
            Document collections' list
        permissions : list | None
            Document permissions' list
        properties : dict | None
            Document's properties
        quality : int
            Document's quality
        metadata_values : dict | None
            Document's metadata values
        raw : bytes | str | None
            Raw metadata payload. When set, parsing is deferred until a field
            accessor is called. Format is auto-detected: a leading ``<`` (after
            whitespace) is treated as XML, anything else as JSON. Once parsed
            the raw form is discarded and ``to_json_string`` / ``to_xml_string``
            re-serialize from the parsed state.
        """
        self._raw: bytes | str | None = raw
        if raw is not None:
            self._collections: list | None = None
            self._permissions: list | None = None
            self._properties: dict | None = None
            self._quality: int | None = None
            self._metadata_values: dict | None = None
        else:
            self._collections = list(set(collections)) if collections else []
            self._permissions = self._get_clean_permissions(permissions)
            self._properties = self._get_clean_dict(properties)
            self._quality = quality
            self._metadata_values = self._get_clean_dict(metadata_values)

    def _ensure_parsed(self) -> None:
        """Materialize parsed fields from the raw payload, then discard raw."""
        if self._collections is not None:
            return
        source = (
            self._raw.decode("utf-8") if isinstance(self._raw, bytes) else self._raw
        )
        kwargs = (
            self._parse_xml(source)
            if source.lstrip().startswith("<")
            else self._parse_json(source)
        )
        self._collections = list(set(kwargs.get("collections") or []))
        self._permissions = self._get_clean_permissions(kwargs.get("permissions"))
        self._properties = self._get_clean_dict(kwargs.get("properties"))
        self._quality = kwargs.get("quality", 0)
        self._metadata_values = self._get_clean_dict(kwargs.get("metadata_values"))
        self._raw = None

    def __eq__(
        self,
        other: Metadata,
    ) -> bool:
        """Verify if Metadata instances are equal.

        Parameters
        ----------
        other : Metadata
            A Metadata instance to compare

        Returns
        -------
        bool
            True if there's no difference between internal Metadata fields.
            Otherwise, False.
        """
        if not isinstance(other, Metadata):
            return False
        self._ensure_parsed()
        collections_diff = set(self._collections).difference(set(other.collections()))
        permissions_diff = set(self._permissions).difference(set(other.permissions()))
        return (
            collections_diff == set()
            and permissions_diff == set()
            and self._properties == other.properties()
            and self._quality == other.quality()
            and self._metadata_values == other.metadata_values()
        )

    def __hash__(
        self,
    ) -> int:
        """Generate a hash value of a Metadata instance.

        Returns
        -------
        int
            A hash value generated using all internal Metadata fields.
        """
        items = self.collections()
        items.extend(self.permissions())
        items.append(self.quality())
        items.append(frozenset(self.properties().items()))
        items.append(frozenset(self.metadata_values().items()))
        return hash(tuple(items))

    def __copy__(
        self,
    ) -> Metadata:
        """Copy Metadata instance, preserving the unparsed raw payload if any."""
        if self._raw is not None:
            return Metadata(raw=self._raw)
        return Metadata(
            collections=self.collections(),
            permissions=self.permissions(),
            properties=self.properties(),
            quality=self.quality(),
            metadata_values=self.metadata_values(),
        )

    def collections(
        self,
    ) -> list:
        """Return document's collections."""
        self._ensure_parsed()
        return self._collections.copy()

    def permissions(
        self,
    ) -> list:
        """Return document's permissions."""
        self._ensure_parsed()
        return [copy.copy(perm) for perm in self._permissions]

    def properties(
        self,
    ) -> dict:
        """Return document's properties."""
        self._ensure_parsed()
        return self._properties.copy()

    def quality(
        self,
    ) -> int:
        """Return document's quality."""
        self._ensure_parsed()
        return self._quality

    def metadata_values(
        self,
    ) -> dict:
        """Return document's metadata values."""
        self._ensure_parsed()
        return self._metadata_values.copy()

    def raw(
        self,
    ) -> bytes | str | None:
        """Return the raw metadata payload, or None if not available.

        Available when the instance was created via ``Metadata(raw=...)`` and
        no field has been read or modified yet. Returns the payload in the
        original type (``bytes`` or ``str``) so consumers can route it to
        bytes-oriented sinks (file writes, multipart bodies) without an
        unnecessary decode/encode round-trip.

        Once a field accessor is called, the raw payload is discarded and
        ``raw()`` returns None; use ``to_json_string()`` / ``to_xml_string()``
        instead.

        Returns
        -------
        bytes | str | None
            The raw payload in its original type, or None if the metadata was
            built from fields or has already been parsed.
        """
        return self._raw

    def set_quality(
        self,
        quality: int,
    ) -> bool:
        """Set document's quality.

        Parameters
        ----------
        quality : int
            A document's new quality

        Returns
        -------
        allow : bool
            True if value provided is an integer. Otherwise, False.
        """
        allow = isinstance(quality, int)
        if allow:
            self._ensure_parsed()
            self._quality = quality
        return allow

    def add_collection(
        self,
        collection: str,
    ) -> bool:
        """Assign a new collection to document.

        Parameters
        ----------
        collection : str
            A document's new collection

        Returns
        -------
        allow : bool
            True if the collection is non-blank value, and it does not appear already
            in document's collections. Otherwise, False.
        """
        allow = (
            collection is not None
            and not re.search("^\\s*$", collection)
            and collection not in self.collections()
        )
        if allow:
            self._collections.append(collection)
        return allow

    def add_permission(
        self,
        role_name: str,
        capability: str,
    ) -> bool:
        """Assign a new permission to document.

        Parameters
        ----------
        role_name : str
            a permission's role name
        capability : str
            a permission's capability

        Returns
        -------
        bool
            True if there's no such capability assigned to this role already, and it is
            a correct one. Otherwise, False.
        """
        allow = role_name is not None and capability is not None
        if allow:
            self._ensure_parsed()
            permission = self._get_permission_for_role(self._permissions, role_name)
            if permission is not None:
                return permission.add_capability(capability)

            self._permissions.append(Permission(role_name, {capability}))
            return True
        return allow

    def put_property(
        self,
        name: str,
        value: str,
    ):
        """Assign a new property to document.

        Parameters
        ----------
        name : str
            A property name
        value : str
            A property value
        """
        if name and value:
            self._ensure_parsed()
            self._properties[name] = value

    def put_metadata_value(
        self,
        name: str,
        value: str,
    ):
        """Assign a new metadata value to document.

        Parameters
        ----------
        name : str
            A metadata name
        value : str
            A metadata value
        """
        if name and value:
            self._ensure_parsed()
            self._metadata_values[name] = value

    def remove_collection(
        self,
        collection: str,
    ) -> bool:
        """Remove a collection from document.

        Parameters
        ----------
        collection : str
            A document's collection

        Returns
        -------
        allow : bool
            True if the collection is assigned to the document. Otherwise, False.
        """
        allow = collection is not None and collection in self.collections()
        if allow:
            self._collections.remove(collection)
        return allow

    def remove_permission(
        self,
        role_name: str,
        capability: str,
    ) -> bool:
        """Remove a permission from document.

        Parameters
        ----------
        role_name : str
            A permission's role name
        capability : str
            A permission's capability

        Returns
        -------
        bool
            True if the capability is assigned to the role for a document.
            Otherwise, False.
        """
        allow = role_name is not None and capability is not None
        if allow:
            self._ensure_parsed()
            permission = self._get_permission_for_role(self._permissions, role_name)
            allow = permission is not None
            if allow:
                success = permission.remove_capability(capability)
                if len(permission.capabilities()) == 0:
                    self._permissions.remove(permission)
                return success
            return allow
        return allow

    def remove_property(
        self,
        name: str,
    ) -> bool:
        """Remove a property from document.

        Parameters
        ----------
        name : str
            A property name

        Returns
        -------
        bool
            True if the document has a property with such name. Otherwise, False.
        """
        self._ensure_parsed()
        return self._properties.pop(name, None) is not None

    def remove_metadata_value(
        self,
        name: str,
    ) -> bool:
        """Remove a metadata value from document.

        Parameters
        ----------
        name : str
            A metadata name

        Returns
        -------
        bool
            True if the document has a metadata with such name. Otherwise, False.
        """
        self._ensure_parsed()
        return self._metadata_values.pop(name, None) is not None

    def to_json_string(
        self,
        indent: int | None = None,
    ) -> str:
        """Return a stringified JSON representation of the Metadata instance.

        When the instance was created from a raw JSON payload and no field has
        been read or modified yet, the original payload is returned without
        re-serialization.

        Parameters
        ----------
        indent : int | None
            A number of spaces per indent level

        Returns
        -------
        str
            Metadata in a stringified JSON representation
        """
        if indent is None and self._raw is not None:
            source = (
                self._raw.decode("utf-8") if isinstance(self._raw, bytes) else self._raw
            )
            stripped = source.lstrip()
            if stripped.startswith(("{", "[")):
                return source
        return json.dumps(self.to_json(), indent=indent)

    def to_json(
        self,
    ) -> dict:
        """Return a JSON representation of the Metadata instance."""
        self._ensure_parsed()
        return {
            self._COLLECTIONS_KEY: self.collections(),
            self._PERMISSIONS_KEY: [p.to_json() for p in self._permissions],
            self._PROPERTIES_KEY: self.properties(),
            self._QUALITY_KEY: self.quality(),
            self._METADATA_VALUES_KEY: self._metadata_values,
        }

    def to_xml_string(
        self,
        indent: int | None = None,
    ) -> str:
        """Return a stringified XML representation of the Metadata instance.

        When the instance was created from a raw XML payload and no field has
        been read or modified yet, the original payload is returned without
        re-serialization.

        Parameters
        ----------
        indent : int | None
            A number of spaces per indent level

        Returns
        -------
        str
            Metadata in a stringified XML representation
        """
        if indent is None and self._raw is not None:
            source = (
                self._raw.decode("utf-8") if isinstance(self._raw, bytes) else self._raw
            )
            if source.lstrip().startswith("<"):
                return source
        metadata_xml = self.to_xml().getroot()
        if indent is None:
            metadata_str = ElemTree.tostring(
                metadata_xml,
                encoding="utf-8",
                method="xml",
                xml_declaration=True,
            )
        else:
            metadata_xml_string = ElemTree.tostring(metadata_xml)
            metadata_xml_minidom = minidom.parseString(metadata_xml_string)
            metadata_str = metadata_xml_minidom.toprettyxml(
                indent=" " * indent,
                encoding="utf-8",
            )
        return _normalize_xml_declaration(metadata_str).decode("ascii")

    def to_xml(
        self,
    ) -> ElemTree.ElementTree:
        """Return an XML representation of the Metadata instance."""
        self._ensure_parsed()
        attrs = {self._RAPI_NS_PREFIX: self._RAPI_NS_URI}
        root = ElemTree.Element(self._METADATA_TAG, attrib=attrs)

        self._to_xml_collections(root)
        self._to_xml_permissions(root)
        self._to_xml_properties(root)
        self._to_xml_quality(root)
        self._to_xml_metadata_values(root)
        return ElemTree.ElementTree(root)

    def _to_xml_collections(
        self,
        root: ElemTree.Element,
    ):
        """Add collections node to Metadata root."""
        parent = ElemTree.SubElement(root, self._COLLECTIONS_TAG)
        for collection in self.collections():
            child = ElemTree.SubElement(parent, self._COLLECTION_TAG)
            child.text = collection

    def _to_xml_permissions(
        self,
        root: ElemTree.Element,
    ):
        """Add permissions node to Metadata root."""
        permissions = ElemTree.SubElement(root, self._PERMISSIONS_TAG)
        for perm in self._permissions:
            for cap in perm.capabilities():
                permission = ElemTree.SubElement(permissions, self._PERMISSION_TAG)
                role_name = ElemTree.SubElement(permission, self._ROLE_NAME_TAG)
                capability = ElemTree.SubElement(permission, self._CAPABILITY_TAG)
                role_name.text = perm.role_name()
                capability.text = cap

    def _to_xml_properties(
        self,
        root: ElemTree.Element,
    ):
        """Add properties node to Metadata root."""
        attrs = {self._PROP_NS_PREFIX: self._PROP_NS_URI}
        properties = ElemTree.SubElement(root, self._PROPERTIES_TAG, attrib=attrs)
        for prop_name, prop_value in self.properties().items():
            property_ = ElemTree.SubElement(properties, prop_name)
            property_.text = prop_value

    def _to_xml_quality(
        self,
        root: ElemTree.Element,
    ):
        """Add quality node to Metadata root."""
        quality = ElemTree.SubElement(root, self._QUALITY_TAG)
        quality.text = str(self.quality())

    def _to_xml_metadata_values(
        self,
        root: ElemTree.Element,
    ):
        """Add metadata values node to Metadata root."""
        values = ElemTree.SubElement(root, self._METADATA_VALUES_TAG)
        for metadata_name, metadata_value in self.metadata_values().items():
            attrs = {self._KEY_ATTR: metadata_name}
            child = ElemTree.SubElement(values, self._METADATA_VALUE_TAG, attrib=attrs)
            child.text = metadata_value

    @classmethod
    def _get_clean_permissions(
        cls,
        source_permissions: list | None,
    ) -> list:
        """Return permissions list without duplicates.

        If source permissions are None, it returns an empty list.

        Parameters
        ----------
        source_permissions : list | None
            Source permissions to clean out.

        Returns
        -------
        permissions : list
            A clean permissions list
        """
        permissions = []
        if source_permissions is None:
            return permissions

        for permission in source_permissions:
            role_name = permission.role_name()
            existing_perm = cls._get_permission_for_role(permissions, role_name)
            if existing_perm is None:
                permissions.append(permission)
            else:
                logger.warning(
                    "Ignoring permission [%s]: role [%s] is already used in [%s]",
                    permission,
                    role_name,
                    existing_perm,
                )
        return permissions

    @staticmethod
    def _get_permission_for_role(
        permissions: list,
        role_name: str,
    ) -> Permission | None:
        """Return permissions assigned to the role provided.

        Parameters
        ----------
        permissions : list
            A permissions list
        role_name : str
            A role name

        Returns
        -------
        Permission | None
            A role's permission if exists. Otherwise, None.
        """
        return next(filter(lambda p: p.role_name() == role_name, permissions), None)

    @staticmethod
    def _get_clean_dict(
        source_dict: dict | None,
    ) -> dict:
        """Return a dictionary with stringified values and removed None values.

        If source dictionary are None, it returns an empty one.

        Parameters
        ----------
        source_dict : dict | None
            A source dictionary to clean out.

        Returns
        -------
        dict
            A clean dictionary
        """
        if not source_dict:
            return {}
        return {k: str(v) for k, v in source_dict.items() if v is not None}


class Permission:
    """A class representing MarkLogic's document permission."""

    READ: str = "read"
    INSERT: str = "insert"
    UPDATE: str = "update"
    UPDATE_NODE: str = "update-node"
    EXECUTE: str = "execute"

    _CAPABILITIES: ClassVar[tuple] = {READ, INSERT, UPDATE, UPDATE_NODE, EXECUTE}

    def __init__(
        self,
        role_name: str,
        capabilities: set,
    ):
        """Initialize a Permission instance.

        Parameters
        ----------
        role_name : str
            A role name
        capabilities : set
            Capabilities set
        """
        self._role_name = role_name
        self._capabilities = {cap for cap in capabilities if cap in self._CAPABILITIES}

    def __eq__(
        self,
        other: Permission,
    ) -> bool:
        """Verify if Permission instances are equal.

        Parameters
        ----------
        other : Permission
            A Permission instance to compare

        Returns
        -------
        bool
            True if there's no difference between internal Permission fields.
            Otherwise, False.
        """
        return (
            isinstance(other, Permission)
            and self._role_name == other._role_name
            and self._capabilities == other._capabilities
        )

    def __hash__(
        self,
    ) -> int:
        """Generate a hash value of a Permission instance.

        Returns
        -------
        int
            A hash value generated using all internal Permission fields.
        """
        items = list(self._capabilities)
        items.append(self._role_name)
        return hash(tuple(items))

    def __repr__(
        self,
    ) -> str:
        """Return a string representation of the Permission instance."""
        return (
            f"Permission("
            f"role_name='{self._role_name}', "
            f"capabilities={self._capabilities})"
        )

    def role_name(
        self,
    ) -> str:
        """Return permission's role name."""
        return self._role_name

    def capabilities(
        self,
    ) -> set:
        """Return permission's capabilities."""
        return self._capabilities.copy()

    def add_capability(
        self,
        capability: str,
    ) -> bool:
        """Assign a new capability to the role.

        Parameters
        ----------
        capability : str
            a permission's capability

        Returns
        -------
        allow : bool
            True if there's no such capability assigned to this role already, and it is
            a correct one. Otherwise, False.
        """
        allow = (
            capability is not None
            and capability in self._CAPABILITIES
            and capability not in self.capabilities()
        )
        if allow:
            self._capabilities.add(capability)
        return allow

    def remove_capability(
        self,
        capability: str,
    ) -> bool:
        """Remove a capability from the role.

        Parameters
        ----------
        capability : str
            a permission's capability

        Returns
        -------
        allow : bool
            True if the capability is assigned to the role.
            Otherwise, False.
        """
        allow = capability is not None and capability in self.capabilities()
        if allow:
            self._capabilities.remove(capability)
        return allow

    def to_json(
        self,
    ) -> dict:
        """Return a JSON representation of the Permission instance."""
        return {
            "role-name": self.role_name(),
            "capabilities": list(self.capabilities()),
        }
