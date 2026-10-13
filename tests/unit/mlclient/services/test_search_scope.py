"""SearchScope inheritance between a scoped search service and its operations."""

import pytest
import respx

from mlclient import AsyncMLClient, MLClient
from mlclient.search.options import SearchOptions
from mlclient.services import (
    AsyncSearchService,
    SearchScope,
    SearchService,
    TransactionService,
)

SEARCH_URL = "http://localhost:8000/v1/search"


def empty_search_route():
    return respx.post(SEARCH_URL).respond(200, content=b"")


def test_empty_scope_sends_no_scope_parameters():
    assert SearchScope().request_params() == {}


def test_scope_parameters_exclude_options():
    scope = SearchScope(database="Documents", options="product-options")

    assert scope.request_params() == {"database": "Documents"}


def test_override_keeps_fields_the_other_scope_leaves_unset():
    base = SearchScope(database="Documents", collection="products")

    assert base.overridden_by(SearchScope(collection="drinks")) == SearchScope(
        database="Documents",
        collection="drinks",
    )


def test_override_with_none_clears_an_inherited_field():
    base = SearchScope(database="Documents", collection="products")

    assert base.overridden_by(SearchScope(collection=None)) == SearchScope(
        database="Documents",
        collection=None,
    )


def test_override_by_nothing_is_the_same_scope():
    base = SearchScope(database="Documents")

    assert base.overridden_by(None) is base


def test_scope_unpacks_a_transaction_mapping():
    transaction = {"txid": "12345", "database": "Documents"}

    assert SearchScope(**transaction).request_params() == transaction


def test_list_restrictions_are_frozen_to_tuples():
    collections = ["products", "drinks"]
    scope = SearchScope(collection=collections, forest_name=["f1"])
    collections.append("snacks")

    assert scope.collection == ("products", "drinks")
    assert scope.forest_name == ("f1",)


def test_inline_options_are_copied():
    options = {"page-length": 5, "constraint": [{"name": "price"}]}
    scope = SearchScope(options=options)
    options["constraint"][0]["name"] = "color"

    assert scope.options == {"page-length": 5, "constraint": [{"name": "price"}]}


def test_options_of_an_unsupported_type_are_rejected():
    with pytest.raises(TypeError) as error:
        SearchScope(options=["page-length"])

    assert str(error.value) == (
        "options must be an installed name, inline dictionary or SearchOptions, "
        "got list"
    )


def test_inline_options_wrapped_in_their_object_are_rejected():
    with pytest.raises(TypeError) as error:
        SearchScope(options={"options": {"page-length": 5}})

    assert str(error.value) == (
        "inline options must be the members of the options object; "
        "pass options['options'] instead of the whole object"
    )


def test_operation_scope_must_be_a_search_scope():
    with MLClient() as ml, pytest.raises(TypeError) as error:
        ml.search.uris(scope={"database": "Documents"})

    assert str(error.value) == "scope must be a SearchScope, got dict"


@pytest.mark.parametrize(
    ("database", "expected"),
    [
        (None, SearchScope(txid="12345")),
        ("Documents", SearchScope(txid="12345", database="Documents")),
    ],
)
def test_service_unpacks_a_transaction_service(database, expected):
    transaction = TransactionService(api=None, txid="12345", database=database)

    with MLClient() as ml:
        assert ml.search(**transaction).scope == expected


def test_calling_the_service_returns_a_narrower_service():
    with MLClient() as ml:
        catalog = ml.search(database="catalog", collection="products")

        assert isinstance(catalog, SearchService)
        assert catalog.scope == SearchScope(database="catalog", collection="products")
        assert ml.search.scope == SearchScope()


def test_narrowing_a_scoped_service_inherits_its_scope():
    options = SearchOptions().control("page-length", 5)
    with MLClient() as ml:
        drinks = ml.search(database="catalog", options=options)(collection="drinks")

        assert drinks.scope == SearchScope(
            database="catalog",
            collection="drinks",
            options=options,
        )


@respx.mock
def test_service_scope_is_sent_with_every_operation():
    route = empty_search_route()

    with MLClient() as ml:
        ml.search(database="catalog", collection=["products", "drinks"]).uris("tea")

    params = route.calls.last.request.url.params
    assert params["database"] == "catalog"
    assert params.get_list("collection") == ["products", "drinks"]


@respx.mock
def test_operation_scope_overrides_the_service_scope_for_one_request():
    route = empty_search_route()

    with MLClient() as ml:
        catalog = ml.search(database="catalog", collection="products")
        catalog.uris("tea", scope=SearchScope(collection=None, directory="/2026/"))
        catalog.uris("tea")

    first, second = (call.request.url.params for call in route.calls)
    assert first["database"] == "catalog"
    assert "collection" not in first
    assert first["directory"] == "/2026/"
    assert second["collection"] == "products"
    assert "directory" not in second


@pytest.mark.asyncio
@respx.mock
async def test_async_service_narrows_and_sends_its_scope():
    route = empty_search_route()

    async with AsyncMLClient() as ml:
        catalog = ml.search(database="catalog")
        assert isinstance(catalog, AsyncSearchService)
        assert catalog.scope == SearchScope(database="catalog")
        assert ml.search.scope == SearchScope()
        await catalog.uris("tea", scope=SearchScope(txid="12345"))

    params = route.calls.last.request.url.params
    assert params["database"] == "catalog"
    assert params["txid"] == "12345"
