import pytest

from mlclient import exceptions
from mlclient.calls import ForestPropertiesPutCall


@pytest.fixture
def default_forest_properties_put_call():
    """Returns an ForestPropertiesPutCall instance"""
    return ForestPropertiesPutCall(
        forest="forest-1",
        body={"forest-name": "custom-forest"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestPropertiesPutCall(
            forest="forest-1",
            body=None)

    expected_msg = ("No request body provided for "
                    "PUT /manage/v2/forests/{id|name}/properties!")
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestPropertiesPutCall(
            forest="forest-1",
            body=" \n")

    expected_msg = ("No request body provided for "
                    "PUT /manage/v2/forests/{id|name}/properties!")
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/forests/1/properties"
    expected__name_endpoint = "/manage/v2/forests/forest-1/properties"
    assert ForestPropertiesPutCall(
        forest="1",
        body={"forest-name": "custom-forest"}).endpoint() == expected__id_endpoint
    assert ForestPropertiesPutCall(
        forest="forest-1",
        body={"forest-name": "custom-forest"}).endpoint() == expected__name_endpoint


def test_method(default_forest_properties_put_call):
    assert default_forest_properties_put_call.method() == "PUT"


def test_parameters(default_forest_properties_put_call):
    assert default_forest_properties_put_call.params() == {}


def test_headers_for_dict_body():
    call = ForestPropertiesPutCall(
        forest="forest-1",
        body={"forest-name": "custom-forest"})
    assert call.headers() == {
        "content-type": "application/json",
    }


def test_headers_for_stringified_dict_body():
    call = ForestPropertiesPutCall(
        forest="forest-1",
        body='{"forest-name": "custom-forest"}')
    assert call.headers() == {
        "content-type": "application/json",
    }


def test_headers_for_xml_body():
    body = '<forest-properties xmlns="http://marklogic.com/manage">' \
           '  <forest-name>custom-forest</forest-name>' \
           '</forest-properties>'
    call = ForestPropertiesPutCall(
        forest="forest-1",
        body=body)
    assert call.headers() == {
        "content-type": "application/xml",
    }


def test_dict_body():
    call = ForestPropertiesPutCall(
        forest="forest-1",
        body={"forest-name": "custom-forest"})
    assert call.body() == {"forest-name": "custom-forest"}


def test_stringified_dict_body():
    call = ForestPropertiesPutCall(
        forest="forest-1",
        body='{"forest-name": "custom-forest"}')
    assert call.body() == {"forest-name": "custom-forest"}


def test_xml_body():
    body = '<forest-properties xmlns="http://marklogic.com/manage">' \
           '  <forest-name>custom-forest</forest-name>' \
           '</forest-properties>'
    call = ForestPropertiesPutCall(
        forest="forest-1",
        body=body)
    assert call.body() == body
