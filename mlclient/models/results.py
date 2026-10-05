"""Parsed CTS results with scores, frequencies and source locations."""

from __future__ import annotations

import xml.etree.ElementTree as ElemTree
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import TypeAlias


ParsedValue: TypeAlias = (
    bytes
    | str
    | int
    | float
    | Decimal
    | bool
    | date
    | datetime
    | dict
    | list
    | ElemTree.ElementTree
    | ElemTree.Element
    | None
)


@dataclass
class SearchHit:
    """A parsed search result with its original hit score and source location.

    Parameters
    ----------
    content : ParsedValue
        Parsed value, retained as-is: XML tree/element, JSON, scalar or bytes.
    score : int
        Native score captured before applying optional result XPath.
    source_uri : str | None
        Source URI when supplied by the server.
    source_path : str | None
        Source path supplied by the caller; retained as-is.
    """

    content: ParsedValue
    score: int = field(kw_only=True)
    source_uri: str | None = field(default=None, kw_only=True)
    source_path: str | None = field(kw_only=True)

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
class ValueHit:
    """A parsed lexicon value and its native lookup frequency.

    Parameters
    ----------
    value : ParsedValue
        Parsed value supplied by MLResponseParser, without further conversion.
    frequency : int
        Native frequency; item/fragment-frequency options determine its meaning.
    """

    value: ParsedValue
    frequency: int = field(kw_only=True)
