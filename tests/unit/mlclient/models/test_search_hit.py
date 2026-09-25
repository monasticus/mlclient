import xml.etree.ElementTree as ET
from decimal import Decimal

import pytest

from mlclient.models import SearchHit


@pytest.mark.parametrize(
    "content",
    [None, False, 0, [], {}, "", "b", b"\x00\xff", Decimal("1.25")],
)
def test_content_is_retained_as_is_without_parsing(content):
    result = SearchHit(content, score=0)
    assert result.content is content


@pytest.mark.parametrize("document", [False, True])
def test_xpath_mirrors_elementtree_and_accepts_namespaces(document):
    element = ET.fromstring(
        '<root xmlns:p="https://monasticus.com/mlclient/examples/test">'
        "<p:child/></root>",
    )
    content = ET.ElementTree(element) if document else element
    hit = SearchHit(content, score=7)
    assert hit.content is content
    assert hit.xpath(
        "p:child",
        p="https://monasticus.com/mlclient/examples/test",
    ) == [element[0]]
    assert hit.xpath("missing") == []
    assert hit.source_uri is None
    assert hit.source_path == "/"


@pytest.mark.parametrize("content", [None, False, 1, {}, [], "abc", b"abc"])
def test_non_xml_xpath_fails_clearly(content):
    with pytest.raises(TypeError, match="XML"):
        SearchHit(content, score=0).xpath("child")


def test_text_content_and_explicit_provenance():
    result = SearchHit(
        "café",
        score=0,
        source_uri="/c.json",
        source_path='/text("a")',
    )
    assert result.content == "café"
    assert result.source_uri == "/c.json"
    assert result.source_path == '/text("a")'
    assert result.score == 0


def test_binary_never_decodes_implicitly():
    result = SearchHit(b"\x00\xff", score=0)
    assert result.content == b"\x00\xff"
