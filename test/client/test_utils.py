import pytest

from client import utils
from client import exceptions


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
