import pytest

from mlclient import exceptions
from mlclient.calls import ValueGetCall


@pytest.fixture
def default_value_get_call():
    """Returns a ValueGetCall instance"""
    return ValueGetCall(name="category")


def test_validation_name_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValueGetCall(name=" ")

    expected_msg = "No values name provided for /v1/values/{name}!"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValueGetCall(name="category", view="none")

    expected_msg = "The supported views are: values, aggregate, all"
    assert err.value.args[0] == expected_msg


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValueGetCall(name="category", data_format="html")

    expected_msg = "The supported formats are: json, xml"
    assert err.value.args[0] == expected_msg


def test_validation_direction_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValueGetCall(name="category", direction="Ascending")

    expected_msg = "The supported directions are: ascending, descending"
    assert err.value.args[0] == expected_msg


def test_validation_frequency_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ValueGetCall(name="category", frequency="Item")

    expected_msg = "The supported frequencies are: item, fragment"
    assert err.value.args[0] == expected_msg


def test_endpoint(default_value_get_call):
    assert default_value_get_call.endpoint == "/v1/values/category"


def test_method(default_value_get_call):
    assert default_value_get_call.method == "GET"


def test_parameters(default_value_get_call):
    assert default_value_get_call.params == {"format": "xml"}


def test_headers(default_value_get_call):
    assert default_value_get_call.headers == {"Accept": "application/xml"}


def test_headers_for_json_format():
    assert ValueGetCall(name="category", data_format="json").headers == {
        "Accept": "application/json",
    }


def test_headers_for_xml_format():
    assert ValueGetCall(name="category", data_format="xml").headers == {
        "Accept": "application/xml",
    }


def test_body(default_value_get_call):
    assert default_value_get_call.body is None


def test_fully_parametrized_call():
    call = ValueGetCall(
        name="price",
        q="coffee",
        structured_query='{"search":{"ctsquery":{"trueQuery":{}}}}',
        options="product-options",
        database="Documents",
        view="aggregate",
        data_format="json",
        collection=["products", "drinks"],
        directory="/products/",
        direction="descending",
        frequency="fragment",
        limit=100,
        start=11,
        page_length=5,
        aggregate="median",
        aggregate_path="native/median",
        transform="values-transform",
        transform_params={"lang": "en"},
        timestamp="16000000000",
        txid="12345",
        forest_name="Documents-1",
    )
    assert call.method == "GET"
    assert call.endpoint == "/v1/values/price"
    assert call.headers == {"Accept": "application/json"}
    assert call.params == {
        "q": "coffee",
        "structuredQuery": '{"search":{"ctsquery":{"trueQuery":{}}}}',
        "options": "product-options",
        "database": "Documents",
        "view": "aggregate",
        "format": "json",
        "collection": ["products", "drinks"],
        "directory": "/products/",
        "direction": "descending",
        "frequency": "fragment",
        "limit": 100,
        "start": 11,
        "pageLength": 5,
        "aggregate": "median",
        "aggregatePath": "native/median",
        "transform": "values-transform",
        "timestamp": "16000000000",
        "txid": "12345",
        "forest-name": "Documents-1",
        "trans:lang": "en",
    }
    assert call.body is None


def test_zero_and_empty_parameters_are_preserved():
    call = ValueGetCall(
        name="price", q="", limit=0, transform_params={"offset": 0, "unused": None},
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
        ValueGetCall(name="category", **params)

    assert err.value.args[0] == expected_msg


def test_endpoint_encodes_the_definition_name():
    call = ValueGetCall(name="price/day?x")

    assert call.endpoint == "/v1/values/price%2Fday%3Fx"
