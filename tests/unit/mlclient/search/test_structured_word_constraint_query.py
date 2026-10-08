"""Test word-constraint-query serialization."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import WordConstraintQuery


def test_serializes_to_json():
    query = WordConstraintQuery("title", ["blue", "green"], weight=2)
    expected = {
        "word-constraint-query": {
            "constraint-name": "title",
            "text": ["blue", "green"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = WordConstraintQuery("title", ["blue", "green"], weight=2)
    expected = ElementTree.fromstring(
        '<word-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>title</constraint-name>"
        "<text>blue</text><text>green</text><weight>2</weight>"
        "</word-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_empty_constraint_name():
    with pytest.raises(ValueError, match=r".+") as exc:
        WordConstraintQuery("", "blue").serialize("xml")
    assert str(exc.value) == (
        "Use one non-empty constraint name; combine queries with OrQuery."
    )


def test_multiple_constraint_names():
    with pytest.raises(ValueError, match=r".+") as exc:
        WordConstraintQuery(["title", "label"], "blue").serialize("xml")
    assert str(exc.value) == (
        "Use one non-empty constraint name; combine queries with OrQuery."
    )
