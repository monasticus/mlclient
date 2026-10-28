import pytest

from mlclient import exceptions
from mlclient.calls import ApiCall, ClusterConfigPostCall

SERVER_CONFIG = (
    '<host xmlns="http://marklogic.com/manage">'
    "<host-name>joining-host.example.com</host-name>"
    "</host>"
)
CLUSTER_CONFIG = b"PK\x03\x04cluster-config"


@pytest.fixture
def default_cluster_config_post_call():
    """Returns a ClusterConfigPostCall instance"""
    return ClusterConfigPostCall(server_config=SERVER_CONFIG, group="Default")


def test_is_api_call():
    assert issubclass(ClusterConfigPostCall, ApiCall)


def test_validation_no_configuration():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ClusterConfigPostCall()

    expected_msg = (
        "You must include either the server_config or the cluster_config parameter!"
    )
    assert err.value.args[0] == expected_msg


def test_validation_both_configurations():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ClusterConfigPostCall(
            server_config=SERVER_CONFIG,
            group="Default",
            cluster_config=CLUSTER_CONFIG,
        )

    expected_msg = (
        "You cannot include both the server_config and the cluster_config parameter!"
    )
    assert err.value.args[0] == expected_msg


def test_validation_server_config_without_group():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ClusterConfigPostCall(server_config=SERVER_CONFIG)

    expected_msg = "The group parameter is required with the server_config parameter!"
    assert err.value.args[0] == expected_msg


def test_validation_cluster_config_with_group():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ClusterConfigPostCall(cluster_config=CLUSTER_CONFIG, group="Default")

    expected_msg = (
        "The group and zone parameters are permitted "
        "only with the server_config parameter!"
    )
    assert err.value.args[0] == expected_msg


def test_validation_cluster_config_with_zone():
    with pytest.raises(exceptions.WrongParametersError) as err:
        ClusterConfigPostCall(cluster_config=CLUSTER_CONFIG, zone="zone-a")

    expected_msg = (
        "The group and zone parameters are permitted "
        "only with the server_config parameter!"
    )
    assert err.value.args[0] == expected_msg


def test_endpoint(default_cluster_config_post_call):
    assert default_cluster_config_post_call.endpoint == "/admin/v1/cluster-config"


def test_method(default_cluster_config_post_call):
    assert default_cluster_config_post_call.method == "POST"


def test_parameters(default_cluster_config_post_call):
    assert default_cluster_config_post_call.params == {}


def test_headers_for_server_config(default_cluster_config_post_call):
    assert default_cluster_config_post_call.headers == {
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_headers_for_cluster_config():
    call = ClusterConfigPostCall(cluster_config=CLUSTER_CONFIG)
    assert call.headers == {
        "Content-Type": "application/zip",
    }


def test_body_for_server_config(default_cluster_config_post_call):
    assert default_cluster_config_post_call.body == {
        "server-config": (
            '<host xmlns="http://marklogic.com/manage">'
            "<host-name>joining-host.example.com</host-name>"
            "</host>"
        ),
        "group": "Default",
    }


def test_body_for_server_config_with_zone():
    call = ClusterConfigPostCall(
        server_config=SERVER_CONFIG,
        group="Default",
        zone="zone-a",
    )
    assert call.body == {
        "server-config": (
            '<host xmlns="http://marklogic.com/manage">'
            "<host-name>joining-host.example.com</host-name>"
            "</host>"
        ),
        "group": "Default",
        "zone": "zone-a",
    }


def test_body_for_cluster_config():
    call = ClusterConfigPostCall(cluster_config=CLUSTER_CONFIG)
    assert call.body == b"PK\x03\x04cluster-config"


def test_fully_parametrized_call():
    call = ClusterConfigPostCall(
        server_config=SERVER_CONFIG,
        group="Analytics",
        zone="zone-a",
    )
    assert call.method == "POST"
    assert call.endpoint == "/admin/v1/cluster-config"
    assert call.headers == {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    assert call.params == {}
    assert call.body == {
        "server-config": (
            '<host xmlns="http://marklogic.com/manage">'
            "<host-name>joining-host.example.com</host-name>"
            "</host>"
        ),
        "group": "Analytics",
        "zone": "zone-a",
    }
