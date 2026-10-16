"""Combined queries preserve both vocabularies and inline search settings."""

from copy import deepcopy

import httpx
import pytest
import respx

from mlclient import AsyncMLClient, MLClient
from mlclient.search.options import opt
from mlclient.search.structured import Element, sq
from mlclient.services import SearchScope
from mlclient.xquery import cts


@pytest.mark.parametrize(
    ("query", "criteria"),
    [
        (sq.term("blue"), {"query": {"queries": [{"term-query": {"text": ["blue"]}}]}}),
        (cts.word_query("blue"), {"ctsquery": {"wordQuery": {"text": ["blue"]}}}),
    ],
    ids=["structured", "cts"],
)
@pytest.mark.parametrize(
    ("kwargs", "members"),
    [
        ({"options": None, "qtext": None}, {}),
        ({"options": {}}, {"options": {}}),
        ({"qtext": ""}, {"qtext": ""}),
        ({"qtext": "coffee"}, {"qtext": "coffee"}),
        (
            {"options": {"page-length": 5}, "qtext": "coffee"},
            {"options": {"page-length": 5}, "qtext": "coffee"},
        ),
        (
            {"options": opt.options(opt.word_constraint("title", Element("title")))},
            {
                "options": {
                    "constraint": [
                        {
                            "name": "title",
                            "word": {"element": {"name": "title", "ns": ""}},
                        },
                    ],
                },
            },
        ),
    ],
    ids=[
        "omitted",
        "empty-options",
        "empty-qtext",
        "qtext",
        "options-and-qtext",
        "options-builder",
    ],
)
def test_combined_query_includes_options_and_qtext(query, criteria, kwargs, members):
    assert query.to_combined_query(**kwargs) == {"search": {**criteria, **members}}


@pytest.mark.parametrize(
    "query",
    [sq.term("blue"), cts.word_query("blue")],
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
    [sq.term("blue"), cts.word_query("blue")],
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
        ({"qtext": 1}, "qtext must be a string or None"),
    ],
    ids=["invalid-options", "installed-name", "wrapped-options", "invalid-qtext"],
)
def test_combined_query_rejects_invalid_options_and_qtext(query, kwargs, message):
    with pytest.raises(TypeError) as error:
        query.to_combined_query(**kwargs)
    assert str(error.value) == message


@pytest.mark.parametrize(
    "query",
    [sq.term("blue"), cts.word_query("blue")],
    ids=["structured", "cts"],
)
@respx.mock
def test_search_sends_combined_query_with_scope_defaults(query):
    combined = query.to_combined_query(options={"page-length": 3}, qtext="coffee")
    expected = deepcopy(combined)
    expected["search"]["options"]["return-facets"] = False
    before = deepcopy(combined)
    respx.post(
        "http://localhost:8000/v1/search",
        params={"format": "json", "pageLength": "3"},
        headers={"Content-Type": "application/json", "Accept": "multipart/mixed"},
        json=expected,
    ).mock(return_value=httpx.Response(200))
    with MLClient() as ml:
        result = ml.search(
            options={"page-length": 8, "return-facets": False},
        ).documents(combined)
    assert result == []
    assert combined == before


@pytest.mark.asyncio
@respx.mock
async def test_async_search_sends_combined_query_with_installed_options():
    combined = sq.term("blue").to_combined_query(
        options={"page-length": 3},
        qtext="coffee",
    )
    respx.post(
        "http://localhost:8000/v1/search",
        params={"format": "json", "pageLength": "3", "options": "catalog"},
        headers={"Content-Type": "application/json", "Accept": "multipart/mixed"},
        json=combined,
    ).mock(return_value=httpx.Response(200))
    async with AsyncMLClient() as ml:
        result = await ml.search(options="catalog").documents(combined)
    assert result == []


@pytest.mark.parametrize(
    ("query", "message"),
    [
        (
            {"unsupported": {}},
            (
                "query dictionary must contain exactly one "
                "search, query or ctsquery dictionary"
            ),
        ),
        (
            {"search": []},
            (
                "query dictionary must contain exactly one "
                "search, query or ctsquery dictionary"
            ),
        ),
        (
            {"search": {}, "qtext": "coffee"},
            (
                "query dictionary must contain exactly one "
                "search, query or ctsquery dictionary"
            ),
        ),
        (
            {"search": {"options": "catalog"}},
            "combined query options must be a dictionary",
        ),
    ],
    ids=["unknown-root", "non-dict-search", "outer-qtext", "non-dict-options"],
)
def test_search_rejects_invalid_combined_query(query, message):
    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search.documents(query)
    assert str(error.value) == message


@pytest.mark.parametrize(
    "query",
    [
        {"ctsquery": {"wordQuery": {"text": "blue"}}},
        cts.word_query("blue").to_combined_query(qtext="coffee"),
    ],
    ids=["cts-json", "combined-json"],
)
def test_values_rejects_raw_cts_json(query):
    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search.values("price", query)
    assert str(error.value) == (
        "raw CTS JSON cannot filter lexicon operations; pass a CTS query object instead"
    )


@respx.mock
def test_values_sends_combined_structured_query():
    options = {"values": [{"name": "uris", "uri": {}}]}
    combined = sq.term("blue").to_combined_query(options=options, qtext="coffee")
    respx.post(
        "http://localhost:8000/v1/values/uris",
        params={"format": "json", "view": "values"},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json=combined,
    ).mock(
        return_value=httpx.Response(
            200,
            json={"values-response": {"name": "uris", "type": "xs:string"}},
        ),
    )
    with MLClient() as ml:
        assert ml.search.values("uris", combined) == []


@pytest.mark.parametrize(
    ("override", "expected_options", "url_options", "page_length"),
    [
        ({"page-length": 2}, {"page-length": 2, "return-facets": False}, None, "2"),
        (
            opt.options(opt.word_constraint("title", Element("title"))),
            {
                "page-length": 3,
                "return-facets": False,
                "constraint": [
                    {"name": "title", "word": {"element": {"name": "title", "ns": ""}}},
                ],
            },
            None,
            "3",
        ),
        (None, None, None, None),
        ("request-options", {"page-length": 3}, "request-options", "3"),
    ],
    ids=["inline", "builder", "clear", "installed"],
)
@respx.mock
def test_request_scope_options_override_combined_query_and_service(
    override,
    expected_options,
    url_options,
    page_length,
):
    combined = sq.term("blue").to_combined_query(options={"page-length": 3})
    expected = {"search": {"query": {"queries": [{"term-query": {"text": ["blue"]}}]}}}
    if expected_options is not None:
        expected["search"]["options"] = expected_options
    params = {"format": "json"}
    if page_length is not None:
        params["pageLength"] = page_length
    if url_options is not None:
        params["options"] = url_options
    respx.post(
        "http://localhost:8000/v1/search",
        params=params,
        json=expected,
    ).mock(return_value=httpx.Response(200))

    with MLClient() as ml:
        documents = ml.search(
            options={"page-length": 8, "return-facets": False},
        ).documents(
            combined,
            scope=SearchScope(options=override),
        )

    assert documents == []


@pytest.mark.parametrize(
    "query",
    [
        {"query": {"term-query": {"text": "blue"}}},
        {"ctsquery": {"wordQuery": {"text": "blue"}}},
    ],
    ids=["structured-json", "cts-json"],
)
@respx.mock
def test_search_accepts_raw_query_json_with_scope_options(query):
    before = deepcopy(query)
    expected = {"search": {**query, "options": {"page-length": 5}}}
    respx.post(
        "http://localhost:8000/v1/search",
        params={"format": "json", "pageLength": "5"},
        headers={"Content-Type": "application/json", "Accept": "multipart/mixed"},
        json=expected,
    ).mock(return_value=httpx.Response(200))

    with MLClient() as ml:
        documents = ml.search(options={"page-length": 5}).documents(query)

    assert documents == []
    assert query == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        {"query": {"term-query": {"text": "blue"}}},
        {"ctsquery": {"wordQuery": {"text": "blue"}}},
    ],
    ids=["structured-json", "cts-json"],
)
@respx.mock
async def test_async_search_accepts_raw_query_json(query):
    respx.post(
        "http://localhost:8000/v1/search",
        params={"format": "json"},
        headers={"Content-Type": "application/json", "Accept": "multipart/mixed"},
        json={"search": query},
    ).mock(return_value=httpx.Response(200))

    async with AsyncMLClient() as ml:
        documents = await ml.search.documents(query)

    assert documents == []


@pytest.mark.parametrize("query", [{"query": []}, {"ctsquery": []}, {}])
def test_search_rejects_invalid_raw_query_json(query):
    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search.documents(query)
    assert str(error.value) == (
        "query dictionary must contain exactly one search, query or ctsquery dictionary"
    )
