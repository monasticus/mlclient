import pytest

from mlclient import exceptions
from mlclient.calls import SearchPostCall

COMBINED_QUERY = {"search": {"ctsquery": {"wordQuery": {"text": ["coffee"]}}}}


@pytest.fixture
def default_search_post_call():
    """Returns a SearchPostCall instance"""
    return SearchPostCall(body=COMBINED_QUERY)


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchPostCall(body=None)

    expected_msg = "No request body provided for POST /v1/search!"
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchPostCall(body=" \n")

    expected_msg = "No request body provided for POST /v1/search!"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchPostCall(body=COMBINED_QUERY, view="bogus")

    expected_msg = "The supported views are: facets, results, metadata, all, none"
    assert err.value.args[0] == expected_msg


def test_validation_category_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchPostCall(body=COMBINED_QUERY, category="X", multipart=True)

    expected_msg = (
        "The supported categories are: "
        "content, metadata, metadata-values, collections, "
        "permissions, properties, quality"
    )
    assert err.value.args[0] == expected_msg


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchPostCall(body=COMBINED_QUERY, data_format="JSON")

    expected_msg = "The supported formats are: json, xml"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_search_post_call):
    assert default_search_post_call.endpoint == "/v1/search"


def test_method(default_search_post_call):
    assert default_search_post_call.method == "POST"


def test_parameters(default_search_post_call):
    assert default_search_post_call.params == {}


def test_headers_for_dict_body():
    assert SearchPostCall(body=COMBINED_QUERY).headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = SearchPostCall(body='{"search": {"qtext": "coffee"}}')
    assert call.headers == {"Content-Type": "application/json"}


def test_headers_for_xml_body():
    call = SearchPostCall(
        body='<search xmlns="http://marklogic.com/appservices/search"/>',
    )
    assert call.headers == {"Content-Type": "application/xml"}


def test_headers_for_none_format():
    assert SearchPostCall(body=COMBINED_QUERY, data_format=None).headers == {
        "Content-Type": "application/json",
    }


def test_headers_for_json_format():
    assert SearchPostCall(body=COMBINED_QUERY, data_format="json").headers == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def test_headers_for_xml_format():
    assert SearchPostCall(body=COMBINED_QUERY, data_format="xml").headers == {
        "Accept": "application/xml",
        "Content-Type": "application/json",
    }


def test_headers_for_multipart():
    assert SearchPostCall(body=COMBINED_QUERY, multipart=True).headers == {
        "Accept": "multipart/mixed",
        "Content-Type": "application/json",
    }


def test_dict_body():
    assert SearchPostCall(body=COMBINED_QUERY).body == COMBINED_QUERY


def test_stringified_dict_body():
    call = SearchPostCall(body='{"search": {"qtext": "coffee"}}')
    assert call.body == {"search": {"qtext": "coffee"}}


def test_xml_body():
    body = '<search xmlns="http://marklogic.com/appservices/search"/>'
    assert SearchPostCall(body=body).body == body


def test_fully_parametrized_call():
    call = SearchPostCall(
        body=COMBINED_QUERY,
        q="tea",
        start=11,
        page_length=5,
        options="product-options",
        view="results",
        category="collections",
        database="Documents",
        data_format="json",
        txid="12345",
        collection="products",
        directory="/products/",
        transform="product-transform",
        transform_params={"lang": "en"},
        timestamp="16000000000",
        forest_name="Documents-1",
        multipart=True,
    )
    assert call.method == "POST"
    assert call.endpoint == "/v1/search"
    assert call.headers == {
        "Accept": "multipart/mixed",
        "Content-Type": "application/json",
    }
    assert call.params == {
        "q": "tea",
        "start": 11,
        "pageLength": 5,
        "options": "product-options",
        "view": "results",
        "category": "collections",
        "database": "Documents",
        "format": "json",
        "txid": "12345",
        "collection": "products",
        "directory": "/products/",
        "transform": "product-transform",
        "timestamp": "16000000000",
        "forest-name": "Documents-1",
        "trans:lang": "en",
    }
    assert call.body == COMBINED_QUERY


def test_zero_and_empty_parameters_are_preserved():
    call = SearchPostCall(
        body={"search": {"qtext": ""}},
        q="",
        page_length=0,
        transform_params={"offset": 0, "unused": None},
    )

    assert call.params == {"q": "", "pageLength": 0, "trans:offset": 0}


@pytest.mark.parametrize("body", ["123", "true", "null", "[1]", '"x"'])
def test_validation_rejects_json_body_that_is_not_an_object(body):
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchPostCall(body)

    assert err.value.args[0] == "POST /v1/search requires a JSON object or XML body"


def test_validation_category_requires_multipart():
    with pytest.raises(exceptions.WrongParametersError) as err:
        SearchPostCall({"search": {}}, category="content")

    assert err.value.args[0] == (
        "category is supported only in a multi-document read (multipart=True)"
    )
