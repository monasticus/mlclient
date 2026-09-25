"""Parsed CTS results with scores, frequencies and source locations."""

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
    """

    content: object

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
    source_uri : str | None
        Source URI when supplied by the server.
    source_path : str
        Source path; '/' is a fallback, not a document-node type assertion.
    """

    score: int = field(kw_only=True)
    source_uri: str | None = field(default=None, kw_only=True)
    source_path: str = field(default="/", kw_only=True)


@dataclass
class ValueHit:
    """A parsed lexicon value and its native lookup frequency.

    Parameters
    ----------
    value : object
        Parsed value supplied by MLResponseParser, without further conversion.
    frequency : int
        Native frequency; item/fragment-frequency options determine its meaning.
    """

    value: object
    frequency: int = field(kw_only=True)
