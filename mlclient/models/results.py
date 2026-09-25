"""Parsed CTS results with optional original payload snapshots."""

from __future__ import annotations

import xml.etree.ElementTree as ElemTree
from dataclasses import dataclass, field


@dataclass
class ResultContent:
    """Content already converted by MLResponseParser, without another parser.

    Parameters
    ----------
    content : object
        Parsed value, retained as-is: XML tree/element, JSON, scalar or bytes.
    content_bytes : bytes | None
        Optional original payload snapshot. CTS services always supply it.
        Mutating content does not rewrite this snapshot.
    encoding : str
        Encoding for decoding the original textual payload, not for parsing it.
    """

    content: object
    content_bytes: bytes | None = field(default=None, kw_only=True, repr=False)
    encoding: str = field(default="utf-8", kw_only=True)

    @property
    def content_string(self) -> str | None:
        """Decode original text, or return None for binary/unavailable bytes."""
        if self.content_bytes is None or isinstance(self.content, bytes):
            return None
        return self.content_bytes.decode(self.encoding)

    def xpath(self, expr: str, **namespaces: str) -> list:
        """Call findall on the already parsed XML tree or element.

        Parameters
        ----------
        expr : str
            ElementTree-supported XPath relative to returned XML content.
        **namespaces : str
            Prefix-to-URI bindings, as in XMLDocument.xpath.

        Returns
        -------
        list
            Matching elements; no parsing or server request occurs here.

        Raises
        ------
        TypeError
            If content is not an XML tree or element.
        SyntaxError
            If ElementTree rejects the local path.
        """
        if not isinstance(self.content, (ElemTree.ElementTree, ElemTree.Element)):
            message = "xpath requires XML document or element content"
            raise TypeError(message)
        return self.content.findall(expr, namespaces or None)


@dataclass
class SearchHit(ResultContent):
    """A parsed search result with its original hit score and source location.

    Parameters
    ----------
    content : object
        Parsed node content supplied by MLResponseParser.
    score : int
        Native score captured before optional projection.
    content_bytes : bytes | None
        Original payload snapshot; supplied by CTS services without reserialization.
    encoding : str
        Original text encoding.
    source_uri : str | None
        Source URI when supplied by the server.
    source_path : str
        Source path; '/' is a fallback, not a document-node type assertion.
    """

    score: int = field(kw_only=True)
    source_uri: str | None = field(default=None, kw_only=True)
    source_path: str = field(default="/", kw_only=True)


@dataclass
class ValueHit(ResultContent):
    """A parsed lexicon value and its native lookup frequency.

    Parameters
    ----------
    content : object
        Parsed value supplied by MLResponseParser, without further conversion.
    frequency : int
        Native frequency; item/fragment-frequency options determine its meaning.
    content_bytes : bytes | None
        Original payload snapshot; supplied by CTS services without reserialization.
    encoding : str
        Original text encoding.
    """

    frequency: int = field(kw_only=True)
