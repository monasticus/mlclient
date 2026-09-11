import pytest

from mlclient import exceptions
from mlclient.calls import GroupPropertiesPutCall


@pytest.fixture
def default_group_properties_put_call():
    """Returns a GroupPropertiesPutCall instance"""
    return GroupPropertiesPutCall(group="Default", body={"file-log-level": "info"})


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupPropertiesPutCall(group="Default", body=None)

    expected_msg = (
        "No request body provided for PUT /manage/v2/groups/{id|name}/properties!"
    )
    assert err.value.args[0] == expected_msg


def test_validation_blank_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        GroupPropertiesPutCall(group="Default", body=" \n")

    expected_msg = (
        "No request body provided for PUT /manage/v2/groups/{id|name}/properties!"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/groups/1/properties"
    expected__name_endpoint = "/manage/v2/groups/Default/properties"
    assert (
        GroupPropertiesPutCall(group="1", body={"file-log-level": "info"}).endpoint
        == expected__id_endpoint
    )
    assert (
        GroupPropertiesPutCall(
            group="Default",
            body={"file-log-level": "info"},
        ).endpoint
        == expected__name_endpoint
    )


def test_method(default_group_properties_put_call):
    assert default_group_properties_put_call.method == "PUT"


def test_parameters(default_group_properties_put_call):
    assert default_group_properties_put_call.params == {}


def test_headers_for_dict_body():
    call = GroupPropertiesPutCall(group="Default", body={"file-log-level": "info"})
    assert call.headers == {"Content-Type": "application/json"}


def test_headers_for_stringified_dict_body():
    call = GroupPropertiesPutCall(group="Default", body='{"file-log-level": "info"}')
    assert call.headers == {"Content-Type": "application/json"}


def test_headers_for_xml_body():
    body = (
        '<group-properties xmlns="http://marklogic.com/manage">'
        "  <file-log-level>info</file-log-level>"
        "</group-properties>"
    )
    call = GroupPropertiesPutCall(group="Default", body=body)
    assert call.headers == {"Content-Type": "application/xml"}


def test_dict_body():
    call = GroupPropertiesPutCall(group="Default", body={"file-log-level": "info"})
    assert call.body == {"file-log-level": "info"}


def test_stringified_dict_body():
    call = GroupPropertiesPutCall(group="Default", body='{"file-log-level": "info"}')
    assert call.body == {"file-log-level": "info"}


def test_xml_body():
    body = (
        '<group-properties xmlns="http://marklogic.com/manage">'
        "  <file-log-level>info</file-log-level>"
        "</group-properties>"
    )
    call = GroupPropertiesPutCall(group="Default", body=body)
    assert call.body == body
