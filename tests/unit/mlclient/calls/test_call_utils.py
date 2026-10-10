import pytest

from mlclient import exceptions
from mlclient.calls import _utils as utils


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
