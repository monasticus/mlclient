"""Test structured-query target serialization."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import PathIndex


def test_path_index_serializes_to_json_with_namespaces():
    query = PathIndex("/r:report/r:price", namespaces={"r": "urn:example:reports"})
    assert query.serialize() == {
        "path-index": {
            "text": "/r:report/r:price",
            "namespaces": {"r": "urn:example:reports"},
        },
    }


def test_path_index_serializes_to_json():
    query = PathIndex("/report/price")
    expected = {"path-index": {"text": "/report/price"}}
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_path_index_serializes_to_xml():
    query = PathIndex("/report/price")
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<path-index>/report/price</path-index>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_path_index_with_namespaces():
    query = PathIndex("/r:report/r:price", {"r": "urn:example:reports"})

    assert ElementTree.tostring(query.serialize("xml"), encoding="unicode") == (
        '<search:path-index xmlns:search="http://marklogic.com/appservices/search" '
        'xmlns:r="urn:example:reports">/r:report/r:price</search:path-index>'
    )


@pytest.mark.parametrize("prefix", ["search", "xml", "xmlns", ""])
def test_path_index_rejects_reserved_or_empty_prefixes(prefix):
    with pytest.raises(ValueError, match="PathIndex namespace prefixes") as exc:
        PathIndex("/x:report", {prefix: "urn:other"})

    assert str(exc.value) == (
        "PathIndex namespace prefixes must be non-empty and not search, xml or xmlns."
    )


def test_path_index_is_hashable_and_keeps_a_copy_of_its_namespaces():
    namespaces = {"r": "urn:example:reports"}
    index = PathIndex("/r:report", namespaces)
    namespaces["r"] = "urn:changed"

    assert index.namespaces == {"r": "urn:example:reports"}
    assert hash(index) == hash(PathIndex("/r:report", {"r": "urn:example:reports"}))
    with pytest.raises(TypeError):
        index.namespaces["r"] = "urn:changed"
