"""Structured and CTS query to_combined_query methods preserve inline settings."""

from copy import deepcopy

import pytest

from mlclient.search.options import SearchOptions, WordConstraint
from mlclient.search.structured import Element, TermQuery
from mlclient.xquery import WordQuery


def test_structured_query_to_combined_query_includes_options_and_qtext():
    query = TermQuery("blue")
    assert query.to_combined_query(options={"page-length": 5}, qtext="coffee") == {
        "search": {
            "query": {"queries": [{"term-query": {"text": ["blue"]}}]},
            "options": {"page-length": 5},
            "qtext": "coffee",
        },
    }


def test_cts_query_to_combined_query_includes_options_and_qtext():
    query = WordQuery("blue")
    assert query.to_combined_query(options={"page-length": 5}, qtext="coffee") == {
        "search": {
            "ctsquery": {"wordQuery": {"text": ["blue"]}},
            "options": {"page-length": 5},
            "qtext": "coffee",
        },
    }


@pytest.mark.parametrize(
    "query",
    [TermQuery("blue"), WordQuery("blue")],
    ids=["structured", "cts"],
)
def test_to_combined_query_accepts_search_options_objects(query):
    options = SearchOptions(WordConstraint("title", Element("title")))
    assert query.to_combined_query(options=options)["search"]["options"] == {
        "constraint": [
            {"name": "title", "word": {"element": {"name": "title", "ns": ""}}},
        ],
    }


@pytest.mark.parametrize(
    "query",
    [TermQuery("blue"), WordQuery("blue")],
    ids=["structured", "cts"],
)
def test_to_combined_query_omits_none_options_and_qtext(query):
    assert (
        query.to_combined_query(options=None, qtext=None) == query.to_combined_query()
    )


@pytest.mark.parametrize(
    "query",
    [TermQuery("blue"), WordQuery("blue")],
    ids=["structured", "cts"],
)
def test_to_combined_query_preserves_empty_options_and_qtext(query):
    combined = query.to_combined_query(options={}, qtext="")
    assert combined["search"]["options"] == {}
    assert combined["search"]["qtext"] == ""


@pytest.mark.parametrize(
    "query",
    [TermQuery("blue"), WordQuery("blue")],
    ids=["structured", "cts"],
)
def test_combined_query_copies_inline_options(query):
    options = {"constraint": [{"name": "c1", "word": {"element": {"name": "text"}}}]}
    expected = deepcopy(options)
    combined = query.to_combined_query(options=options)
    options["constraint"][0]["name"] = "changed-input"
    assert combined["search"]["options"] == expected
    combined["search"]["options"]["constraint"][0]["name"] = "changed-output"
    assert query.to_combined_query(options=expected)["search"]["options"] == expected


@pytest.mark.parametrize(
    "query",
    [TermQuery("blue"), WordQuery("blue")],
    ids=["structured", "cts"],
)
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {"options": 1},
            (
                "options must be inline members without an options wrapper "
                "or SearchOptions"
            ),
        ),
        (
            {"options": "installed-options"},
            (
                "options must be inline members without an options wrapper "
                "or SearchOptions"
            ),
        ),
        (
            {"options": {"options": {}}},
            (
                "options must be inline members without an options wrapper "
                "or SearchOptions"
            ),
        ),
        (
            {"options": TermQuery("blue")},
            (
                "options must be inline members without an options wrapper "
                "or SearchOptions"
            ),
        ),
        ({"qtext": 1}, "qtext must be a string or None"),
    ],
    ids=[
        "invalid-options",
        "installed-name",
        "wrapped-options",
        "query-as-options",
        "invalid-qtext",
    ],
)
def test_combined_query_rejects_invalid_options_and_qtext(query, kwargs, message):
    with pytest.raises(TypeError) as error:
        query.to_combined_query(**kwargs)
    assert str(error.value) == message
