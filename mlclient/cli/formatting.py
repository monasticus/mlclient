"""Formatting of structured CLI response payloads."""

from __future__ import annotations

import json
from xml.dom import minidom
from xml.parsers.expat import ExpatError


def prettify(text: str, content_type: str | None = None) -> str:
    """Indent valid structured responses without hiding malformed response bodies.

    Parameters
    ----------
    text : str
        Decoded response body or evaluation result
    content_type : str | None, default None
        Response media type. When omitted, detect JSON objects/arrays and XML
        from the text; other evaluation values remain unchanged.

    Returns
    -------
    str
        JSON/XML indented by two spaces, or unchanged text when unsuitable
    """
    if not text:
        return text
    if content_type is None:
        stripped = text.lstrip()
        if stripped.startswith(("{", "[")):
            content_type = "application/json"
        elif stripped.startswith("<"):
            content_type = "application/xml"
        else:
            return text
    try:
        if "json" in content_type.lower():
            return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
        if "xml" in content_type.lower():
            return _prettify_xml(text)
    except (ValueError, ExpatError):
        return text
    return text


def _prettify_xml(text: str) -> str:
    """Re-indent XML while preserving its declaration and significant whitespace.

    Whitespace-only text nodes between elements are dropped first; left in, the
    server's own indentation turns into blank lines under toprettyxml.
    Mixed content and explicit whitespace preservation retain the original text.

    Parameters
    ----------
    text : str
        XML response text

    Returns
    -------
    str
        Indented element-only XML or the original whitespace-sensitive XML

    Raises
    ------
    ExpatError
        If the input is not well-formed XML
    """
    dom = minidom.parseString(text)
    for element in dom.getElementsByTagName("*"):
        if element.getAttribute("xml:space") == "preserve" or (
            any(child.nodeType == child.ELEMENT_NODE for child in element.childNodes)
            and any(
                child.nodeType in (child.TEXT_NODE, child.CDATA_SECTION_NODE)
                and (child.data.strip() or (child.data and "\n" not in child.data))
                for child in element.childNodes
            )
        ):
            return text
    _strip_blank_text_nodes(dom)
    body = dom.toprettyxml(indent="  ").partition("\n")[2].rstrip("\n")
    if text.startswith("<?xml") and text[5:6].isspace():
        declaration = text.partition("?>")[0] + "?>"
        return declaration + "\n" + body
    return body


def _strip_blank_text_nodes(node: minidom.Node) -> None:
    """Remove indentation around child elements, preserving leaf text.

    Parameters
    ----------
    node : minidom.Node
        DOM subtree to modify in place
    """
    has_elements = any(item.nodeType == item.ELEMENT_NODE for item in node.childNodes)
    for child in list(node.childNodes):
        if (
            child.nodeType == child.TEXT_NODE
            and not child.data.strip()
            and has_elements
        ):
            node.removeChild(child)
        else:
            _strip_blank_text_nodes(child)
