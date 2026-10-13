import pytest

from mlclient import exceptions
from mlclient.calls import ValuePostCall

COMBINED_QUERY = {
    "search": {
        "ctsquery": {"collectionQuery": {"uris": ["products"]}},
        "options": {"values": [{"name": "uris", "uri": None}]},
    },
}


@pytest.fixture
def default_value_post_call():
    """Returns a ValuePostCall instance"""
    return ValuePostCall(name="uris", body=COMBINED_QUERY)


def test_validation_name_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="", body=COMBINED_QUERY)

    expected_msg = "No values name provided for /v1/values/{name}!"
    assert err.value.args[0] == expected_msg


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="uris", body=None)

    expected_msg = "No request body provided for POST /v1/values/{name}!"
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="uris", body="\n ")

    expected_msg = "No request body provided for POST /v1/values/{name}!"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="uris", body=COMBINED_QUERY, view="bogus")

    expected_msg = "The supported views are: values, aggregate, all"
    assert err.value.args[0] == expected_msg


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="uris", body=COMBINED_QUERY, data_format="text")

    expected_msg = "The supported formats are: json, xml"
    assert err.value.args[0] == expected_msg


def test_validation_direction_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="uris", body=COMBINED_QUERY, direction="up")

    expected_msg = "The supported directions are: ascending, descending"
    assert err.value.args[0] == expected_msg


def test_validation_frequency_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="uris", body=COMBINED_QUERY, frequency="document")

    expected_msg = "The supported frequencies are: item, fragment"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_value_post_call):
    assert default_value_post_call.endpoint == "/v1/values/uris"


def test_method(default_value_post_call):
    assert default_value_post_call.method == "POST"


def test_parameters(default_value_post_call):
    assert default_value_post_call.params == {"format": "xml"}


def test_headers_for_dict_body():
    assert ValuePostCall(name="uris", body=COMBINED_QUERY).headers == {
        "Accept": "application/xml",
        "Content-Type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = ValuePostCall(name="uris", body='{"search": {"qtext": "coffee"}}')
    assert call.headers == {
        "Accept": "application/xml",
        "Content-Type": "application/json",
    }


def test_headers_for_xml_body():
    call = ValuePostCall(
        name="uris",
        body='<search xmlns="http://marklogic.com/appservices/search"/>',
    )
    assert call.headers == {
        "Accept": "application/xml",
        "Content-Type": "application/xml",
    }


def test_headers_for_json_format():
    call = ValuePostCall(name="uris", body=COMBINED_QUERY, data_format="json")
    assert call.headers == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def test_dict_body():
    assert ValuePostCall(name="uris", body=COMBINED_QUERY).body == COMBINED_QUERY


def test_stringified_dict_body():
    call = ValuePostCall(name="uris", body='{"search": {"qtext": "coffee"}}')
    assert call.body == {"search": {"qtext": "coffee"}}


def test_xml_body():
    body = '<search xmlns="http://marklogic.com/appservices/search"/>'
    assert ValuePostCall(name="uris", body=body).body == body


def test_fully_parametrized_call():
    call = ValuePostCall(
        name="uris",
        body=COMBINED_QUERY,
        q="coffee",
        options="product-options",
        database="Documents",
        view="values",
        data_format="json",
        txid="12345",
        collection="products",
        direction="ascending",
        directory="/products/",
        frequency="item",
        limit=100,
        start=11,
        page_length=5,
        aggregate="count",
        aggregate_path="native/count",
        transform="values-transform",
        transform_params={"lang": "en"},
        timestamp="16000000000",
        forest_name=["Documents-1", "Documents-2"],
    )
    assert call.method == "POST"
    assert call.endpoint == "/v1/values/uris"
    assert call.headers == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    assert call.params == {
        "q": "coffee",
        "options": "product-options",
        "database": "Documents",
        "view": "values",
        "format": "json",
        "txid": "12345",
        "collection": "products",
        "direction": "ascending",
        "directory": "/products/",
        "frequency": "item",
        "limit": 100,
        "start": 11,
        "pageLength": 5,
        "aggregate": "count",
        "aggregatePath": "native/count",
        "transform": "values-transform",
        "timestamp": "16000000000",
        "forest-name": ["Documents-1", "Documents-2"],
        "trans:lang": "en",
    }
    assert call.body == COMBINED_QUERY


def test_zero_and_empty_parameters_are_preserved():
    call = ValuePostCall(
        name="price",
        body={"search": {"qtext": ""}},
        q="",
        limit=0,
        transform_params={"offset": 0, "unused": None},
    )

    assert call.params == {"q": "", "format": "xml", "limit": 0, "trans:offset": 0}


@pytest.mark.parametrize(
    ("params", "expected_msg"),
    [
        ({"view": ""}, "The supported views are: values, aggregate, all"),
        ({"data_format": ""}, "The supported formats are: json, xml"),
        ({"direction": ""}, "The supported directions are: ascending, descending"),
        ({"frequency": ""}, "The supported frequencies are: item, fragment"),
    ],
)
def test_validation_rejects_blank_enumerated_params(params, expected_msg):
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="category", body={"search": {}}, **params)

    assert err.value.args[0] == expected_msg


def test_endpoint_encodes_the_definition_name():
    call = ValuePostCall(name="price/day?x", body={"search": {}})

    assert call.endpoint == "/v1/values/price%2Fday%3Fx"


@pytest.mark.parametrize("body", ["123", "[1]", '"x"'])
def test_validation_rejects_json_body_that_is_not_an_object(body):
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValuePostCall(name="category", body=body)

    assert err.value.args[0] == (
        "POST /v1/values/{name} requires a JSON object or XML body"
    )
