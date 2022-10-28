import pytest

from mlclient import exceptions, utils


def test_get_accept_header_for_xml_format():
    xml_accept_header = utils.get_accept_header_for_format("xml")
    assert xml_accept_header == "application/xml"


def test_get_accept_header_for_json_format():
    json_accept_header = utils.get_accept_header_for_format("json")
    assert json_accept_header == "application/json"


def test_get_accept_header_for_html_format():
    html_accept_header = utils.get_accept_header_for_format("html")
    assert html_accept_header == "text/html"


def test_get_accept_header_for_text_format():
    text_accept_header = utils.get_accept_header_for_format("text")
    assert text_accept_header == "text/plain"


def test_get_accept_header_for_unsupported_format():
    with pytest.raises(exceptions.UnsupportedFormat) as err:
        utils.get_accept_header_for_format("xxx")

    assert err.value.args[0] == "Provided format [xxx] is not supported."


def test_get_content_type_header_for_xml_data():
    xml_content_type_header = utils.get_content_type_header_for_data("<root></root>")
    assert xml_content_type_header == "application/xml"


def test_get_content_type_header_for_json_data():
    json_content_type_header = utils.get_content_type_header_for_data({"key": "value"})
    assert json_content_type_header == "application/json"


def test_get_content_type_header_for_stringified_json_data():
    json_content_type_header = utils.get_content_type_header_for_data('{"key": "value"}')
    assert json_content_type_header == "application/json"
