from __future__ import annotations

import pytest

from mlclient.cli.formatting import prettify


@pytest.mark.parametrize(
    "content_type",
    [
        None,
        "application/json",
        "Application/JSON; charset=utf-8",
        "application/problem+json",
    ],
)
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            '  {"name":"zażółć","items":[1,true,null]}',
            '{\n  "name": "zażółć",\n  "items": [\n    1,\n    true,\n    null\n  ]\n}',
        ),
        ("[1,2]", "[\n  1,\n  2\n]"),
    ],
)
def test_prettify_json(text, expected, content_type):
    assert prettify(text, content_type) == expected


@pytest.mark.parametrize("content_type", [None, "application/xml", "text/xml"])
@pytest.mark.parametrize(
    "text",
    ["<root><item>one</item></root>", "<root>\n    <item>one</item>\n</root>"],
)
def test_prettify_xml_reindents_without_adding_declaration(text, content_type):
    assert prettify(text, content_type) == "<root>\n  <item>one</item>\n</root>"


@pytest.mark.parametrize(
    "declaration",
    [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        "<?xml version='1.0'?>",
    ],
)
def test_prettify_preserves_xml_declaration_verbatim(declaration):
    assert prettify(declaration + "<root><item/></root>") == (
        declaration + "\n<root>\n  <item/>\n</root>"
    )


@pytest.mark.parametrize(
    "text",
    [
        "<p>Hello <b>world</b>!</p>",
        "<root><p> <b>one</b> </p></root>",
        "<root><![CDATA[hello]]><item/></root>",
        '<root><item xml:space="preserve">  <value/>  </item></root>',
    ],
)
def test_prettify_preserves_whitespace_sensitive_xml(text):
    assert prettify(text) == text


def test_prettify_preserves_xml_leaf_whitespace():
    assert prettify("<root><item>  </item></root>") == (
        "<root>\n  <item>  </item>\n</root>"
    )


@pytest.mark.parametrize(
    ("text", "content_type"),
    [
        ("", None),
        ("", "application/json"),
        ("   ", None),
        ("   ", "application/xml"),
        ("{broken", None),
        ("broken json", "application/json"),
        ("<broken>", None),
        ("<broken>", "application/xml"),
        ("plain text", None),
        ('{"a":1}', "text/plain"),
        ("<root><item/></root>", "text/plain"),
        ("42", None),
        ("true", None),
        ("null", None),
        ('"hello"', None),
    ],
)
def test_prettify_leaves_unsuitable_text_unchanged(text, content_type):
    assert prettify(text, content_type) == text
