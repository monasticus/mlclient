"""Exercise the common serialization contract with both native vocabularies."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import cts
from mlclient.search import QueryComponent, SearchQuery
from mlclient.search.structured import sq


def test_structured_query_component():
    query: QueryComponent = sq.term("blue")
    assert isinstance(query, QueryComponent)
    assert query.serialize() == {"term-query": {"text": ["blue"]}}
    assert query.to_json() == {"term-query": {"text": ["blue"]}}
    assert tostring(query.serialize("xml")) == (
        b'<search:term-query xmlns:search="http://marklogic.com/appservices/search">'
        b"<search:text>blue</search:text></search:term-query>"
    )
    assert tostring(query.to_xml()) == (
        b'<search:term-query xmlns:search="http://marklogic.com/appservices/search">'
        b"<search:text>blue</search:text></search:term-query>"
    )


def test_cts_query_component():
    query: QueryComponent = cts.word_query("blue")
    assert isinstance(query, QueryComponent)
    assert query.serialize() == {"wordQuery": {"text": ["blue"]}}
    assert query.to_json() == {"wordQuery": {"text": ["blue"]}}
    assert tostring(query.serialize("xml")) == (
        b'<cts:word-query xmlns:cts="http://marklogic.com/cts">'
        b"<cts:text>blue</cts:text></cts:word-query>"
    )
    assert tostring(query.to_xml()) == (
        b'<cts:word-query xmlns:cts="http://marklogic.com/cts">'
        b"<cts:text>blue</cts:text></cts:word-query>"
    )


def test_structured_query_combined_query():
    query: SearchQuery = sq.term("blue")
    assert query.to_combined_query() == {
        "search": {"query": {"queries": [{"term-query": {"text": ["blue"]}}]}},
    }


def test_structured_query_wrapper_combined_query():
    query: SearchQuery = sq.query(sq.term("blue"), sq.collection("reports"))
    assert query.to_combined_query() == {
        "search": {
            "query": {
                "queries": [
                    {"term-query": {"text": ["blue"]}},
                    {"collection-query": {"uri": ["reports"]}},
                ],
            },
        },
    }


def test_cts_query_combined_query():
    query: SearchQuery = cts.and_query(
        [cts.collection_query("reports"), cts.word_query("blue")],
    )
    assert query.to_combined_query() == {
        "search": {
            "ctsquery": {
                "andQuery": {
                    "queries": [
                        {"collectionQuery": {"uris": ["reports"]}},
                        {"wordQuery": {"text": ["blue"]}},
                    ],
                },
            },
        },
    }
