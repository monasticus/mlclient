import pytest

from mlclient.calls import SearchDeleteCall
from mlclient.exceptions import WrongParametersError


@pytest.fixture
def default_search_delete_call():
    """Returns a SearchDeleteCall instance"""
    return SearchDeleteCall(collection="products")


def test_endpoint(default_search_delete_call):
    assert default_search_delete_call.endpoint == "/v1/search"


def test_method(default_search_delete_call):
    assert default_search_delete_call.method == "DELETE"


def test_parameters(default_search_delete_call):
    assert default_search_delete_call.params == {"collection": "products"}


def test_parameters_clearing_database():
    assert SearchDeleteCall(clear_database=True).params == {}


def test_parameters_clearing_named_database():
    call = SearchDeleteCall(database="Documents", clear_database=True)

    assert call.params == {"database": "Documents"}


@pytest.mark.parametrize(
    "params",
    [{}, {"database": "Documents"}, {"txid": "12345"}],
)
def test_clearing_database_requires_confirmation(params):
    with pytest.raises(WrongParametersError) as error:
        SearchDeleteCall(**params)

    assert str(error.value) == (
        "DELETE /v1/search without a collection or directory removes every "
        "document in the database; pass clear_database=True to confirm"
    )


@pytest.mark.parametrize(
    "params",
    [{"collection": "products"}, {"directory": "/products/"}],
)
def test_clearing_database_excludes_filters(params):
    with pytest.raises(WrongParametersError) as error:
        SearchDeleteCall(**params, clear_database=True)

    assert str(error.value) == (
        "clear_database=True removes every document in the database "
        "and cannot be combined with a collection or directory"
    )


def test_headers(default_search_delete_call):
    assert default_search_delete_call.headers == {}


def test_body(default_search_delete_call):
    assert default_search_delete_call.body is None


@pytest.mark.parametrize("name", ["database", "txid", "collection", "directory"])
@pytest.mark.parametrize("value", ["", "  \n"])
def test_blank_parameters_are_rejected(name, value):
    with pytest.raises(WrongParametersError) as error:
        SearchDeleteCall(**{"collection": "products", name: value})

    assert str(error.value) == f"{name} must not be blank in DELETE /v1/search"


@pytest.mark.parametrize("name", ["collection", "directory"])
@pytest.mark.parametrize("value", [[], (), ["products"], ("products",), {}, 0, False])
def test_non_string_filters_are_rejected(name, value):
    with pytest.raises(WrongParametersError) as error:
        SearchDeleteCall(**{name: value})

    assert str(error.value) == f"{name} must be a string in DELETE /v1/search"


def test_fully_parametrized_call():
    call = SearchDeleteCall(
        database="Documents",
        txid="12345",
        directory="/products/",
    )
    assert call.method == "DELETE"
    assert call.endpoint == "/v1/search"
    assert call.headers == {}
    assert call.params == {
        "database": "Documents",
        "txid": "12345",
        "directory": "/products/",
    }
    assert call.body is None
