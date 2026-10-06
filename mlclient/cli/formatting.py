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

    Re-indent element-only content while leaving mixed content and subtrees with
    explicit whitespace preservation unindented.

    Parameters
    ----------
    text : str
        XML response text

    Returns
    -------
    str
        XML with indentation only outside whitespace-sensitive subtrees

    Raises
    ------
    ExpatError
        If the input is not well-formed XML
    """
    dom = minidom.parseString(text)
    body = "\n".join(_format_xml_node(child) for child in dom.childNodes)
    if text.startswith("<?xml") and text[5:6].isspace():
        declaration = text.partition("?>")[0] + "?>"
        return declaration + "\n" + body
    return body


def _format_xml_node(node: minidom.Node, indent: str = "") -> str:
    """Indent a node without inserting whitespace inside sensitive subtrees.

    Parameters
    ----------
    node : minidom.Node
        DOM subtree to serialize
    indent : str, default ""
        Indentation before the node

    Returns
    -------
    str
        Serialized node, with two-space indentation for element-only content
    """
    if node.nodeType != node.ELEMENT_NODE:
        return indent + node.toxml()
    has_elements = any(item.nodeType == item.ELEMENT_NODE for item in node.childNodes)
    if (
        not has_elements
        or node.getAttribute("xml:space") == "preserve"
        or any(
            child.nodeType in (child.TEXT_NODE, child.CDATA_SECTION_NODE)
            and (child.data.strip() or (child.data and "\n" not in child.data))
            for child in node.childNodes
        )
    ):
        return indent + node.toxml()
    opening = node.cloneNode(deep=False).toxml()[:-2] + ">"
    children = "\n".join(
        _format_xml_node(child, indent + "  ")
        for child in node.childNodes
        if child.nodeType != child.TEXT_NODE or child.data.strip()
    )
    return f"{indent}{opening}\n{children}\n{indent}</{node.tagName}>"
