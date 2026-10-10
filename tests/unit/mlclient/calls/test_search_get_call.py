import pytest

from mlclient import exceptions
from mlclient.calls import SearchGetCall


@pytest.fixture
def default_search_get_call():
    """Returns a SearchGetCall instance"""
    return SearchGetCall()


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchGetCall(view="Results")

    expected_msg = "The supported views are: facets, results, metadata, all, none"
    assert err.value.args[0] == expected_msg


def test_validation_category_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchGetCall(category="X", multipart=True)

    expected_msg = (
        "The supported categories are: "
        "content, metadata, metadata-values, collections, "
        "permissions, properties, quality"
    )
    assert err.value.args[0] == expected_msg


def test_validation_multiple_categories_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchGetCall(category=["content", "X"], multipart=True)

    expected_msg = (
        "The supported categories are: "
        "content, metadata, metadata-values, collections, "
        "permissions, properties, quality"
    )
    assert err.value.args[0] == expected_msg


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchGetCall(data_format="text")

    expected_msg = "The supported formats are: json, xml"
    assert err.value.args[0] == expected_msg


@pytest.mark.parametrize(
    ("params", "expected_msg"),
    [
        ({"view": ""}, "The supported views are: facets, results, metadata, all, none"),
        ({"data_format": ""}, "The supported formats are: json, xml"),
        (
            {"category": "", "multipart": True},
            "The supported categories are: "
            "content, metadata, metadata-values, collections, "
            "permissions, properties, quality",
        ),
    ],
)
def test_validation_rejects_blank_enumerated_params(params, expected_msg):
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchGetCall(**params)

    assert err.value.args[0] == expected_msg


def test_validation_category_requires_multipart():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchGetCall(category="content")

    assert err.value.args[0] == (
        "category is supported only in a multi-document read (multipart=True)"
    )


def test_endpoint(default_search_get_call):
    assert default_search_get_call.endpoint == "/v1/search"


def test_method(default_search_get_call):
    assert default_search_get_call.method == "GET"


def test_parameters(default_search_get_call):
    assert default_search_get_call.params == {}


def test_parameters_string_query():
    assert SearchGetCall(q="coffee AND tea").params == {"q": "coffee AND tea"}


def test_parameters_structured_query():
    query = '{"search":{"ctsquery":{"wordQuery":{"text":["coffee"]}}}}'
    assert SearchGetCall(structured_query=query).params == {
        "structuredQuery": query,
    }


def test_parameters_multiple_categories():
    assert SearchGetCall(
        category=["content", "collections"],
        multipart=True,
    ).params == {"category": ["content", "collections"]}


def test_parameters_categories_as_tuple():
    call = SearchGetCall(category=("content", "metadata"), multipart=True)

    assert call.params == {"category": ["content", "metadata"]}


def test_parameters_collections_and_forests_as_tuples():
    call = SearchGetCall(collection=("a", "b"), forest_name=("f1",))

    assert call.params == {"collection": ["a", "b"], "forest-name": ["f1"]}


def test_headers(default_search_get_call):
    assert default_search_get_call.headers == {}


def test_headers_for_none_format():
    assert SearchGetCall(data_format=None).headers == {}


def test_headers_for_json_format():
    assert SearchGetCall(data_format="json").headers == {
        "Accept": "application/json",
    }


def test_headers_for_xml_format():
    assert SearchGetCall(data_format="xml").headers == {
        "Accept": "application/xml",
    }


def test_headers_for_multipart():
    assert SearchGetCall(multipart=True).headers == {
        "Accept": "multipart/mixed",
    }


def test_headers_for_multipart_with_json_format():
    assert SearchGetCall(data_format="json", multipart=True).headers == {
        "Accept": "multipart/mixed",
    }


def test_body(default_search_get_call):
    assert default_search_get_call.body is None


def test_fully_parametrized_call():
    call = SearchGetCall(
        q="coffee",
        structured_query='{"query":{"queries":[]}}',
        start=11,
        page_length=5,
        options="product-options",
        view="none",
        category=["content", "metadata"],
        database="Documents",
        data_format="json",
        txid="12345",
        collection=["products", "drinks"],
        directory="/products/",
        transform="product-transform",
        transform_params={"lang": "en"},
        timestamp="16000000000",
        forest_name=["Documents-1", "Documents-2"],
        multipart=True,
    )
    assert call.method == "GET"
    assert call.endpoint == "/v1/search"
    assert call.headers == {"Accept": "multipart/mixed"}
    assert call.params == {
        "q": "coffee",
        "structuredQuery": '{"query":{"queries":[]}}',
        "start": 11,
        "pageLength": 5,
        "options": "product-options",
        "view": "none",
        "category": ["content", "metadata"],
        "database": "Documents",
        "format": "json",
        "txid": "12345",
        "collection": ["products", "drinks"],
        "directory": "/products/",
        "transform": "product-transform",
        "timestamp": "16000000000",
        "forest-name": ["Documents-1", "Documents-2"],
        "trans:lang": "en",
    }
    assert call.body is None


def test_zero_and_empty_parameters_are_preserved():
    call = SearchGetCall(
        q="", page_length=0, transform_params={"offset": 0, "unused": None},
    )

    assert call.params == {"q": "", "pageLength": 0, "trans:offset": 0}
