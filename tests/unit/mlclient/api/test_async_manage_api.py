from pathlib import Path

import httpx
import pytest
import respx

from mlclient import AsyncMLClient
from mlclient.calls import DatabasesGetCall
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


@pytest.mark.asyncio
@respx.mock
async def test_custom_call():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.call(DatabasesGetCall())

    assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_get_logs():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-logs.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/logs")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "ErrorLog.txt")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.logs.get("ErrorLog.txt", data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert "logfile" in resp.json()


@pytest.mark.asyncio
@respx.mock
async def test_get_databases():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-databases.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.databases.get_list(data_format="json")

    expected_uri = "/manage/v2/databases?view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["database-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_post_databases():
    body = '<database-properties xmlns="http://marklogic.com/manage" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-databases.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.databases.create(body)

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert (
        "Payload has errors in structure, content-type or values. "
        "Database name missing."
    ) in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_database():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-database.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/Documents")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.databases.get("Documents", data_format="json")

    expected_uri = "/manage/v2/databases/Documents?view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["database-default"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_post_database():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-database.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/Documents")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"operation": "clear-database"})
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.databases.post(
            "Documents", {"operation": "clear-database"},
        )

    assert resp.status_code == httpx.codes.OK
    assert not resp.text


@pytest.mark.asyncio
@respx.mock
async def test_delete_database():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.databases.delete("custom-db")

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert not resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_database_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-database-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/databases/Documents/properties",
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.databases.get_properties(
            database="Documents",
            data_format="json",
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.json()["database-name"] == "Documents"


@pytest.mark.asyncio
@respx.mock
async def test_put_database_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-database-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/databases/non-existing-db/properties",
    )
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"database-name": "custom-db"})
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_put()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.databases.put_properties(
            "non-existing-db",
            {"database-name": "custom-db"},
        )

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHDB"


@pytest.mark.asyncio
@respx.mock
async def test_get_servers():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-servers.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.servers.get_list(data_format="json")

    expected_uri = "/manage/v2/servers?view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["server-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_post_servers():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-servers.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_param("server-type", "http")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.servers.create(
            '<http-server-properties xmlns="http://marklogic.com/manage" />',
            group_id="Default",
            server_type="http",
        )

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert (
        "Payload has errors in structure, content-type or values. Server name missing."
    ) in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_server():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-server.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers/App-Services")
    ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.servers.get(
            server="App-Services",
            group_id="Default",
            data_format="json",
        )

    expected_uri = "/manage/v2/servers/App-Services?group-id=Default&view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["server-default"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_delete_server():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-delete-server.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers/Non-existing-server")
    ml_mocker.with_request_param("group-id", "Non-existing-group")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.servers.delete(
            "Non-existing-server",
            "Non-existing-group",
        )

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert "No such group Non-existing-group" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_server_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-server-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/servers/App-Services/properties",
    )
    ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.servers.get_properties(
            server="App-Services",
            group_id="Default",
            data_format="json",
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.json()["server-name"] == "App-Services"


@pytest.mark.asyncio
@respx.mock
async def test_put_server_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-server-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/servers/non-existing-server/properties",
    )
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_param("group-id", "non-existing-group")
    ml_mocker.with_request_body({"server-name": "non-existing-server"})
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_put()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.servers.put_properties(
            "non-existing-server",
            "non-existing-group",
            {"server-name": "non-existing-server"},
        )

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHGROUP"


@pytest.mark.asyncio
@respx.mock
async def test_get_forests():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-forests.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/forests")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_request_param("database-id", "Documents")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.forests.get_list(
            data_format="json", database="Documents",
        )

    expected_uri = "/manage/v2/forests?view=default&database-id=Documents"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["forest-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_post_forests():
    body = '<forest-create xmlns="http://marklogic.com/manage" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-forests.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/forests")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.forests.create(body)

    assert resp.status_code == httpx.codes.INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@respx.mock
async def test_put_forests():
    body = '<forest-migrate xmlns="http://marklogic.com/manage" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-forests.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/forests")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_put()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.forests.put(body)

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert (
        "Payload has errors in structure, content-type or values. "
        "Cannot validate payload, no forests specified."
    ) in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_forest():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-forest.json",
    )

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/forests/Documents")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.forests.get("Documents", data_format="json")

    expected_uri = "/manage/v2/forests/Documents?view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["forest-default"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_post_forest():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-forest.xml",
    )

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/forests/forest-01")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"state": "clear"})
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.forests.post("forest-01", {"state": "clear"})

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert "XDMP-NOSUCHFOREST" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_delete_forest():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/forests/forest-01")
    ml_mocker.with_request_param("level", "full")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.forests.delete("forest-01", level="full")

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert not resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_forest_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-forest-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/forests/Documents/properties",
    )
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.forests.get_properties(
            forest="Documents",
            data_format="json",
        )

    assert resp.status_code == httpx.codes.OK
    assert resp.json()["forest-name"] == "Documents"


@pytest.mark.asyncio
@respx.mock
async def test_put_forest_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-forest-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/forests/non-existing-forest/properties",
    )
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"forest-name": "custom-forest"})
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_put()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.forests.put_properties(
            "non-existing-forest",
            {"forest-name": "custom-forest"},
        )

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHFOREST"


@pytest.mark.asyncio
@respx.mock
async def test_get_roles():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-roles.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/roles")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.roles.get_list(data_format="json")

    expected_uri = "/manage/v2/roles?view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["role-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_post_roles():
    body = '<role-properties xmlns="http://marklogic.com/manage/role/properties" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-roles.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/roles")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.roles.create(body)

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert "Payload has errors in structure, content-type or values." in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_role():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-role.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/roles/admin")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.roles.get("admin", data_format="json")

    expected_uri = "/manage/v2/roles/admin?view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["role-default"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_delete_role():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/roles/custom-role")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.roles.delete("custom-role")

    assert resp.status_code == httpx.codes.NO_CONTENT
    assert not resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_role_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-role-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/roles/admin/properties")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.roles.get_properties(role="admin", data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert resp.json()["role-name"] == "admin"


@pytest.mark.asyncio
@respx.mock
async def test_put_role_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-role-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/roles/non-existing-role/properties",
    )
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"role-name": "custom-db"})
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_put()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.roles.put_properties(
            "non-existing-role",
            {"role-name": "custom-db"},
        )

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert (
        "Payload has errors in structure, content-type or values. "
        "Role non-existing-role does not exist or is not accessible"
    ) in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_users():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-users.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/users")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.users.get_list(data_format="json")

    expected_uri = "/manage/v2/users?view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["user-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_post_users():
    body = '<user-properties xmlns="http://marklogic.com/manage/user/properties" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-users.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/users")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.users.create(body)

    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert "Payload has errors in structure, content-type or values." in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_user():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-user.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/users/admin")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("view", "default")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.users.get("admin", data_format="json")

    expected_uri = "/manage/v2/users/admin?view=default"
    assert resp.status_code == httpx.codes.OK
    assert resp.json()["user-default"]["meta"]["uri"] == expected_uri


@pytest.mark.asyncio
@respx.mock
async def test_delete_user():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-delete-user.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/users/custom-user")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_delete()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.users.delete("custom-user")

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert "User does not exist: custom-user" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_user_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-user-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/users/admin/properties")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.users.get_properties(user="admin", data_format="json")

    assert resp.status_code == httpx.codes.OK
    assert resp.json()["user-name"] == "admin"


@pytest.mark.asyncio
@respx.mock
async def test_put_user_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-user-properties.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/users/non-existing-user/properties",
    )
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"user-name": "custom-db"})
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_put()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.users.put_properties(
            "non-existing-user",
            {"user-name": "custom-db"},
        )

    assert resp.status_code == httpx.codes.NOT_FOUND
    assert resp.json()["errorResponse"]["messageCode"] == "SEC-USERDNE"
