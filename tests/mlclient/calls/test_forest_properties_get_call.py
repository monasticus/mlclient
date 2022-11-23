import pytest

from mlclient import exceptions
from mlclient.calls import ForestPropertiesGetCall


@pytest.fixture
def default_forest_properties_get_call():
    """Returns an ForestPropertiesGetCall instance"""
    return ForestPropertiesGetCall(forest="custom-forest")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        ForestPropertiesGetCall(forest="custom-forest", data_format="text")

    assert err.value.args[0] == "The supported formats are: xml, json, html"


def test_endpoint():
    expected__id_endpoint = "/manage/v2/forests/1/properties"
    expected__name_endpoint = "/manage/v2/forests/custom-forest/properties"
    assert ForestPropertiesGetCall(forest="1").endpoint() == expected__id_endpoint
    assert ForestPropertiesGetCall(forest="custom-forest").endpoint() == expected__name_endpoint


def test_method(default_forest_properties_get_call):
    assert default_forest_properties_get_call.method() == "GET"


def test_parameters(default_forest_properties_get_call):
    assert default_forest_properties_get_call.params() == {
        "format": "xml"
    }


def test_headers(default_forest_properties_get_call):
    assert default_forest_properties_get_call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_none_format():
    call = ForestPropertiesGetCall(forest="custom-forest", data_format=None)
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_html_format():
    call = ForestPropertiesGetCall(forest="custom-forest", data_format="html")
    assert call.headers() == {
        "accept": "text/html"
    }


def test_headers_for_xml_format():
    call = ForestPropertiesGetCall(forest="custom-forest", data_format="xml")
    assert call.headers() == {
        "accept": "application/xml"
    }


def test_headers_for_json_format():
    call = ForestPropertiesGetCall(forest="custom-forest", data_format="json")
    assert call.headers() == {
        "accept": "application/json"
    }


def test_body(default_forest_properties_get_call):
    assert default_forest_properties_get_call.body() is None


def test_fully_parametrized_call():
    call = ForestPropertiesGetCall(forest="custom-forest",
                                   data_format="json")
    assert call.method() == "GET"
    assert call.headers() == {
        "accept": "application/json"
    }
    assert call.params() == {
        "format": "json"
    }
    assert call.body() is None
