import pytest

from mlclient import _utils as utils
from mlclient import exceptions
from mlclient._utils import _BiDict
from mlclient.exceptions import ResourceNotFoundError


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


def test_get_accept_header_for_format_case_insensitive():
    json_header = utils.get_accept_header_for_format("JSON")
    xml_header = utils.get_accept_header_for_format("Xml")
    assert json_header == "application/json"
    assert xml_header == "application/xml"


def test_get_accept_header_for_unsupported_format():
    with pytest.raises(exceptions.UnsupportedFormatError) as err:
        utils.get_accept_header_for_format("xxx")

    expected_msg = "Provided format [xxx] is not supported."
    assert err.value.args[0] == expected_msg


def test_get_content_type_header_for_xml_data():
    data = "<root></root>"
    xml_content_type_header = utils.get_content_type_header_for_data(data)
    assert xml_content_type_header == "application/xml"


def test_get_content_type_header_for_json_data():
    data = {"key": "value"}
    json_content_type_header = utils.get_content_type_header_for_data(data)
    assert json_content_type_header == "application/json"


def test_get_content_type_header_for_stringified_json_data():
    data = '{"key": "value"}'
    json_content_type_header = utils.get_content_type_header_for_data(data)
    assert json_content_type_header == "application/json"


@pytest.mark.parametrize("value", [None, "json", ["json", "xml"], ("xml",)])
def test_validate_supported_accepts_supported_or_omitted_values(value):
    utils.validate_supported(value, ["json", "xml"], "formats")


@pytest.mark.parametrize("value", ["", "text", ["json", ""], ("JSON",)])
def test_validate_supported_rejects_other_values(value):
    with pytest.raises(exceptions.WrongParametersError) as err:
        utils.validate_supported(value, ["json", "xml"], "formats")

    assert err.value.args[0] == "The supported formats are: json, xml"


def test_validate_supported_rejects_an_omitted_required_value():
    with pytest.raises(exceptions.WrongParametersError):
        utils.validate_supported(None, ["json", "xml"], "formats", required=True)


def test_query_params_keep_zero_and_empty_values_and_prefix_transforms():
    params = utils.query_params(
        {"q": "", "start": 0, "options": None},
        {"offset": 0, "unused": None},
    )

    assert params == {"q": "", "start": 0, "trans:offset": 0}


def test_query_params_without_transform_params():
    assert utils.query_params({"view": "all"}, None) == {"view": "all"}


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ({"search": {}}, ({"search": {}}, "application/json")),
        ('{"search": {}}', ({"search": {}}, "application/json")),
        ("<search/>", ("<search/>", "application/xml")),
    ],
)
def test_request_body_with_content_type(body, expected):
    assert utils.request_body_with_content_type(body, "POST /v1/search") == expected


@pytest.mark.parametrize("body", [None, "", " \n"])
def test_request_body_must_not_be_blank(body):
    with pytest.raises(exceptions.WrongParametersError) as err:
        utils.request_body_with_content_type(body, "POST /v1/search")

    assert err.value.args[0] == "No request body provided for POST /v1/search!"


@pytest.mark.parametrize("body", ["1", "[]", '"text"', "null"])
def test_json_request_body_must_be_an_object(body):
    with pytest.raises(exceptions.WrongParametersError) as err:
        utils.request_body_with_content_type(body, "POST /v1/search")

    assert err.value.args[0] == "POST /v1/search requires a JSON object or XML body"


def test_get_resource_existing():
    with utils.get_resource("mimetypes.yaml") as resource:
        assert resource.name.endswith("resources/mimetypes.yaml")


def test_get_resource_non_existing():
    with pytest.raises(ResourceNotFoundError) as err:
        utils.get_resource("non-existing-file.yaml")

    assert err.value.args[0] == "No such resource: [non-existing-file.yaml]"


def test_bidict_forward():
    bi_dict = _BiDict({"a": 1})
    assert bi_dict.get("a") == 1


def test_bidict_inverse():
    bi_dict = _BiDict({"a": 1})
    assert bi_dict.get(1) == "a"


def test_bidict_default_none():
    bi_dict = _BiDict({"a": 1})
    assert bi_dict.get("b") is None


def test_bidict_default_custom():
    bi_dict = _BiDict({"a": 1})
    assert bi_dict.get("b", 2) == 2
