import pytest

from mlclient import exceptions
from mlclient.calls import ForestGetCall


@pytest.fixture
def default_forest_get_call():
    """Returns an ForestGetCall instance"""
    return ForestGetCall(forest="custom-forest")


def test_validation_format_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestGetCall(
            forest="custom-forest",
            data_format="text")

    expected_msg = "The supported formats are: xml, json, html"
    assert err.value.args[0] == expected_msg


def test_validation_view_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ForestGetCall(
            forest="custom-forest",
            view="X")

    expected_msg = ("The supported views are: "
                    "describe, default, config, counts, edit, status, "
                    "storage, xdmp:forest-status, properties-schema")
    assert err.value.args[0] == expected_msg


def test_endpoint():
    assert ForestGetCall(
        forest="1").endpoint() == "/manage/v2/forests/1"
    assert ForestGetCall(
        forest="custom-forest").endpoint() == "/manage/v2/forests/custom-forest"


def test_method(default_forest_get_call):
    assert default_forest_get_call.method() == "GET"


def test_parameters(default_forest_get_call):
    assert default_forest_get_call.params() == {
        "format": "xml",
        "view": "default",
    }


def test_headers(default_forest_get_call):
    assert default_forest_get_call.headers() == {
        "accept": "application/xml",
    }


def test_headers_for_none_format():
    call = ForestGetCall(
        forest="custom-forest",
        data_format=None)
    assert call.headers() == {
        "accept": "application/xml",
    }


def test_headers_for_html_format():
    call = ForestGetCall(
        forest="custom-forest",
        data_format="html")
    assert call.headers() == {
        "accept": "text/html",
    }


def test_headers_for_xml_format():
    call = ForestGetCall(
        forest="custom-forest",
        data_format="xml")
    assert call.headers() == {
        "accept": "application/xml",
    }


def test_headers_for_json_format():
    call = ForestGetCall(
        forest="custom-forest",
        data_format="json")
    assert call.headers() == {
        "accept": "application/json",
    }


def test_body(default_forest_get_call):
    assert default_forest_get_call.body() is None


def test_fully_parametrized_call():
    call = ForestGetCall(
        forest="custom-forest",
        data_format="json",
        view="counts")
    assert call.method() == "GET"
    assert call.headers() == {
        "accept": "application/json",
    }
    assert call.params() == {
        "format": "json",
        "view": "counts",
    }
    assert call.body() is None
