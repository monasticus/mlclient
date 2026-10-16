import pytest

from mlclient import exceptions
from mlclient.calls import HostPostCall


@pytest.fixture
def default_host_post_call():
    """Returns a HostPostCall instance"""
    return HostPostCall(host="ml-host.example.com", body={"state": "restart"})


def test_validation_no_state_param_in_body():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostPostCall(host="ml-host.example.com", body={"failover": "true"})

    expected_msg = "You must include the 'state' parameter within a body!"
    assert err.value.args[0] == expected_msg


def test_validation_state_param_in_body():
    with pytest.raises(exceptions.WrongParametersError) as err:
        HostPostCall(host="ml-host.example.com", body={"state": "clear"})

    expected_msg = "The supported states are: shutdown, restart"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    body = {"state": "restart"}
    expected_id_endpoint = "/manage/v2/hosts/13544732455686476949"
    expected_name_endpoint = "/manage/v2/hosts/ml-host.example.com"
    assert (
        HostPostCall(host="13544732455686476949", body=body).endpoint
        == expected_id_endpoint
    )
    assert (
        HostPostCall(host="ml-host.example.com", body=body).endpoint
        == expected_name_endpoint
    )


def test_method(default_host_post_call):
    assert default_host_post_call.method == "POST"


def test_parameters(default_host_post_call):
    assert default_host_post_call.params == {}


def test_headers(default_host_post_call):
    assert default_host_post_call.headers == {
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_body(default_host_post_call):
    assert default_host_post_call.body == {"state": "restart"}


def test_body_with_failover():
    call = HostPostCall(
        host="ml-host.example.com",
        body={"state": "shutdown", "failover": "true"},
    )
    assert call.body == {"state": "shutdown", "failover": "true"}
