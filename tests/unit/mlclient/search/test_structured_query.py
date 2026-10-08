"""Test Query through the public structured-query API."""

from xml.etree import ElementTree

import pytest

from mlclient.search.structured import CollectionQuery, QtextQuery, Query, TermQuery


def test_query_json_is_independent_of_xml(mocker):
    for query_type in (Query, TermQuery, CollectionQuery):
        mocker.patch.object(query_type, "to_xml", side_effect=AssertionError)
    query = Query([TermQuery("blue"), CollectionQuery("reports")])
    assert query.serialize() == {
        "query": {
            "queries": [
                {"term-query": {"text": ["blue"]}},
                {"collection-query": {"uri": ["reports"]}},
            ],
        },
    }


def test_query_xml_is_independent_of_json(mocker):
    for query_type in (Query, TermQuery, CollectionQuery):
        mocker.patch.object(query_type, "to_json", side_effect=AssertionError)
    query = Query([TermQuery("blue"), CollectionQuery("reports")])
    expected = ElementTree.fromstring(
        '<query xmlns="http://marklogic.com/appservices/search">'
        "<term-query><text>blue</text></term-query>"
        "<collection-query><uri>reports</uri></collection-query>"
        "</query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_query_json_with_qtext():
    assert Query(QtextQuery("blue AND green")).serialize() == {
        "query": {"queries": [{"qtext": {"_value": "blue AND green"}}]},
    }


def test_query_serializes_to_xml():
    query = Query([TermQuery("blue"), CollectionQuery("reports")])
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<query>"
        "<term-query>"
        "<text>blue</text>"
        "</term-query>"
        "<collection-query>"
        "<uri>reports</uri>"
        "</collection-query>"
        "</query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_query_serializes_to_json_by_default():
    query = Query([TermQuery("blue"), CollectionQuery("reports")])
    assert query.serialize() == {
        "query": {
            "queries": [
                {"term-query": {"text": ["blue"]}},
                {"collection-query": {"uri": ["reports"]}},
            ],
        },
    }


def test_query_serialization_returns_independent_trees():
    query = Query(TermQuery("blue"))
    first = query.serialize("xml")
    first.clear()

    expected = ElementTree.fromstring(
        '<query xmlns="http://marklogic.com/appservices/search">'
        "<term-query><text>blue</text></term-query>"
        "</query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_query_serialization_returns_independent_json():
    query = Query(TermQuery("blue"))
    first = query.serialize()
    first["query"]["queries"].clear()
    assert query.serialize() == {
        "query": {"queries": [{"term-query": {"text": ["blue"]}}]},
    }


def test_query_serialization_rejects_unknown_format():
    with pytest.raises(ValueError, match=r".+") as exc:
        Query(TermQuery("blue")).serialize("yaml")
    assert str(exc.value) == "Query format must be json or xml."


def test_empty_query_serializes_to_json():
    assert Query([]).serialize() == {"query": {"queries": []}}


def test_query_rejects_nonquery():
    with pytest.raises(TypeError) as exc:
        Query("blue")

    assert str(exc.value) == (
        "Subqueries must be StructuredQuery instances, not Query wrappers."
    )


def test_query_rejects_nested_wrapper():
    with pytest.raises(TypeError) as exc:
        Query(Query(TermQuery("blue")))

    assert str(exc.value) == (
        "Subqueries must be StructuredQuery instances, not Query wrappers."
    )
