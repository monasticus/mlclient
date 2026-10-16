import httpx
import pytest
import respx

from mlclient import AsyncMLClient
from mlclient.calls import TimestampGetCall
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

SERVER_CONFIG = (
    '<host xmlns="http://marklogic.com/manage">'
    "<host-name>joining-host.example.com</host-name>"
    "</host>"
)


@pytest.mark.asyncio
@respx.mock
async def test_custom_call():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.call(TimestampGetCall())

    assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_get_timestamp():
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-get-timestamp.txt",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_content_type("text/plain; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.get_timestamp()

    assert resp.status_code == httpx.codes.OK
    assert "2024-01-15T10:30:00.000Z" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_head_timestamp():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.head_timestamp()

    assert resp.status_code == httpx.codes.OK
    assert resp.content == b""


@pytest.mark.asyncio
@respx.mock
async def test_get_server_config():
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-get-server-config.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/server-config")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.get_server_config()

    assert resp.status_code == httpx.codes.OK
    assert "server-config" in resp.text
    assert "localhost" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_post_init():
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-post-init.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/init")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_response_code(202)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_header("Location", "/admin/v1/timestamp")
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.post_init(data_format="json")

    assert resp.status_code == httpx.codes.ACCEPTED
    assert resp.headers["Location"] == "/admin/v1/timestamp"
    assert resp.json()["restart"]["link"] == {
        "kindref": "timestamp",
        "uriref": "/admin/v1/timestamp",
    }


@pytest.mark.asyncio
@respx.mock
async def test_post_init_with_license():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/init")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body(
        {"license-key": "1234-5678-90AB", "licensee": "Example Licensee"},
    )
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.post_init(
            body={"license-key": "1234-5678-90AB", "licensee": "Example Licensee"},
        )

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""


@pytest.mark.asyncio
@respx.mock
async def test_post_instance_admin():
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-post-instance-admin.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/instance-admin")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body(
        {"admin-username": "admin", "admin-password": "admin", "realm": "public"},
    )
    ml_mocker.with_response_code(202)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_header("Location", "/admin/v1/timestamp")
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.post_instance_admin(
            {"admin-username": "admin", "admin-password": "admin", "realm": "public"},
            data_format="json",
        )

    assert resp.status_code == httpx.codes.ACCEPTED
    assert resp.headers["Location"] == "/admin/v1/timestamp"
    assert resp.json()["restart"]["message"] == (
        "Check for new timestamp to verify host restart."
    )


@pytest.mark.asyncio
@respx.mock
async def test_post_cluster_config():
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-post-cluster-config.zip",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/cluster-config")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "server-config": SERVER_CONFIG,
            "group": "Default",
            "zone": "zone-a",
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/zip")
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.post_cluster_config(
            server_config=SERVER_CONFIG,
            group="Default",
            zone="zone-a",
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.headers["Content-Type"] == "application/zip"
    assert resp.content == response_body


@pytest.mark.asyncio
@respx.mock
async def test_post_cluster_config_to_joining_host():
    cluster_config = resources_utils.read_test_resource_bytes(
        __file__,
        "test-post-cluster-config.zip",
    )
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-post-cluster-config-to-joining-host.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/cluster-config")
    ml_mocker.with_request_content_type("application/zip")
    ml_mocker.with_request_body(cluster_config)
    ml_mocker.with_response_code(202)
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_header("Location", "/admin/v1/timestamp")
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.post_cluster_config(cluster_config=cluster_config)

    assert resp.status_code == httpx.codes.ACCEPTED
    assert resp.headers["Location"] == "/admin/v1/timestamp"
    assert "<uriref>/admin/v1/timestamp</uriref>" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_delete_host_config():
    response_body = resources_utils.read_test_resource_bytes(
        __file__,
        "test-delete-host-config.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/host-config")
    ml_mocker.with_response_code(202)
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_body(response_body)
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.delete_host_config()

    assert resp.status_code == httpx.codes.ACCEPTED
    assert "<uriref>/admin/v1/timestamp</uriref>" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_delete_host_config_of_remote_host():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/host-config")
    ml_mocker.with_request_param("remote-host", "departing-host.example.com")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.delete_host_config(
            remote_host="departing-host.example.com",
        )

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""
