import xml.etree.ElementTree as ET

import pytest

from mlclient.models import SearchHit, ValueHit


def test_value_hit():
    hit = ValueHit("value", frequency=3)

    assert hit.value == "value"
    assert hit.frequency == 3


def test_search_hit():
    hit = SearchHit("content", score=7, source_uri="/a.xml", source_path="/root")

    assert hit.content == "content"
    assert hit.score == 7
    assert hit.source_uri == "/a.xml"
    assert hit.source_path == "/root"


def test_xpath_on_document():
    root = ET.fromstring('<root xmlns:p="urn:test"><p:child /></root>')
    hit = SearchHit(ET.ElementTree(root), score=7, source_path="/")

    assert hit.xpath("p:child", p="urn:test") == [root[0]]


def test_xpath_on_element():
    root = ET.fromstring("<root><child /></root>")
    hit = SearchHit(root, score=7, source_path="/")

    assert hit.xpath("child") == [root[0]]


def test_xpath_rejects_json():
    hit = SearchHit({"child": "value"}, score=7, source_path="/")

    with pytest.raises(TypeError, match="XML"):
        hit.xpath("child")
