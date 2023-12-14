from pathlib import Path

import pytest
import responses

from mlclient import MLResourcesClient
from mlclient.calls.model import DocumentsBodyPart
from tests.utils import MLResponseBuilder
from tests.utils import resources as resources_utils


@pytest.fixture()
def xquery():
    return """xquery version '1.0-ml';

    declare variable $element as element() external;

    <new-parent>{$element/child::element()}</new-parent>
    """


@responses.activate()
def test_eval(xquery):
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_body(
        {
            "xquery": "xquery version '1.0-ml';"
            " declare variable $element as element() external;"
            " <new-parent>{$element/child::element()}</new-parent>",
            "vars": '{"element": "<parent><child/></parent>"}',
        },
    )
    builder.with_response_body_multipart_mixed()
    builder.with_response_status(200)
    builder.with_response_body_part("element()", "<new-parent><child/></new-parent>")
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.eval(
            xquery=xquery,
            variables={"element": "<parent><child/></parent>"},
        )

    assert resp.status_code == 200
    assert "<new-parent><child/></new-parent>" in resp.text


@responses.activate()
def test_get_logs():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-logs.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "ErrorLog.txt")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_logs(filename="ErrorLog.txt", data_format="json")

    assert resp.status_code == 200
    assert "logfile" in resp.json()


@responses.activate()
def test_get_databases():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-databases.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/databases")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_databases(data_format="json")

    expected_uri = "/manage/v2/databases?view=default"
    assert resp.status_code == 200
    assert resp.json()["database-default-list"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_post_databases():
    body = '<database-properties xmlns="http://marklogic.com/manage" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-databases.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/databases")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(400)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.post_databases(body=body)

    assert resp.status_code == 400
    assert (
        "Payload has errors in structure, content-type or values. "
        "Database name missing."
    ) in resp.text


@responses.activate()
def test_get_database():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-database.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/databases/Documents")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_database(database="Documents", data_format="json")

    expected_uri = "/manage/v2/databases/Documents?view=default"
    assert resp.status_code == 200
    assert resp.json()["database-default"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_post_database():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-database.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/databases/Documents")
    builder.with_request_content_type("application/json")
    builder.with_request_body({"operation": "clear-database"})
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.post_database(
            database="Documents",
            body={"operation": "clear-database"},
        )

    assert resp.status_code == 200
    assert not resp.text


@responses.activate()
def test_delete_database():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/databases/custom-db")
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    with MLResourcesClient() as client:
        resp = client.delete_database(database="custom-db")

    assert resp.status_code == 204
    assert not resp.text


@responses.activate()
def test_get_database_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-database-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(
        "http://localhost:8002/manage/v2/databases/Documents/properties",
    )
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_database_properties(database="Documents", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["database-name"] == "Documents"


@responses.activate()
def test_put_database_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-database-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(
        "http://localhost:8002/manage/v2/databases/non-existing-db/properties",
    )
    builder.with_request_content_type("application/json")
    builder.with_request_body({"database-name": "custom-db"})
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_put()

    with MLResourcesClient() as client:
        resp = client.put_database_properties(
            database="non-existing-db",
            body={"database-name": "custom-db"},
        )

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHDB"


@responses.activate()
def test_get_servers():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-servers.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/servers")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_servers(data_format="json")

    expected_uri = "/manage/v2/servers?view=default"
    assert resp.status_code == 200
    assert resp.json()["server-default-list"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_post_servers():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-servers.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/servers")
    builder.with_request_param("group-id", "Default")
    builder.with_request_param("server-type", "http")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(400)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.post_servers(
            group_id="Default",
            server_type="http",
            body='<http-server-properties xmlns="http://marklogic.com/manage" />',
        )

    assert resp.status_code == 400
    assert (
        "Payload has errors in structure, content-type or values. "
        "Server name missing."
    ) in resp.text


@responses.activate()
def test_get_server():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-server.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/servers/App-Services")
    builder.with_request_param("group-id", "Default")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_server(
            server="App-Services",
            group_id="Default",
            data_format="json",
        )

    expected_uri = "/manage/v2/servers/App-Services?group-id=Default&view=default"
    assert resp.status_code == 200
    assert resp.json()["server-default"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_delete_server():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-delete-server.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/servers/Non-existing-server")
    builder.with_request_param("group-id", "Non-existing-group")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    with MLResourcesClient() as client:
        resp = client.delete_server(
            server="Non-existing-server",
            group_id="Non-existing-group",
        )

    assert resp.status_code == 404
    assert "No such group Non-existing-group" in resp.text


@responses.activate()
def test_get_server_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-server-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(
        "http://localhost:8002/manage/v2/servers/App-Services/properties",
    )
    builder.with_request_param("group-id", "Default")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_server_properties(
            server="App-Services",
            group_id="Default",
            data_format="json",
        )

    assert resp.status_code == 200
    assert resp.json()["server-name"] == "App-Services"


@responses.activate()
def test_put_server_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-server-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(
        "http://localhost:8002/manage/v2/servers/non-existing-server/properties",
    )
    builder.with_request_content_type("application/json")
    builder.with_request_param("group-id", "non-existing-group")
    builder.with_request_body({"server-name": "non-existing-server"})
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_put()

    with MLResourcesClient() as client:
        resp = client.put_server_properties(
            server="non-existing-server",
            group_id="non-existing-group",
            body={"server-name": "non-existing-server"},
        )

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHGROUP"


@responses.activate()
def test_get_forests():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-forests.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/forests")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_request_param("database-id", "Documents")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_forests(data_format="json", database="Documents")

    expected_uri = "/manage/v2/forests?view=default&database-id=Documents"
    assert resp.status_code == 200
    assert resp.json()["forest-default-list"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_post_forests():
    body = '<forest-create xmlns="http://marklogic.com/manage" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-forests.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/forests")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.post_forests(body=body)

    assert resp.status_code == 500


@responses.activate()
def test_put_forests():
    body = '<forest-migrate xmlns="http://marklogic.com/manage" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-forests.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/forests")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(400)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_put()

    with MLResourcesClient() as client:
        resp = client.put_forests(body=body)

    assert resp.status_code == 400
    assert (
        "Payload has errors in structure, content-type or values. "
        "Cannot validate payload, no forests specified."
    ) in resp.text


@responses.activate()
def test_get_forest():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-forest.json",
    )

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/forests/Documents")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_forest(forest="Documents", data_format="json")

    expected_uri = "/manage/v2/forests/Documents?view=default"
    assert resp.status_code == 200
    assert resp.json()["forest-default"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_post_forest():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-forest.xml",
    )

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/forests/aaa")
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_body({"state": "clear"})
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.post_forest(forest="aaa", body={"state": "clear"})
        MLResponseBuilder.generate_builder_code(resp, True, __file__)

    assert resp.status_code == 404
    assert "XDMP-NOSUCHFOREST" in resp.text


@responses.activate()
def test_delete_forest():
    builder = MLResponseBuilder()
    builder.with_method("DELETE")
    builder.with_base_url("http://localhost:8002/manage/v2/forests/aaa")
    builder.with_request_param("level", "full")
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build()

    with MLResourcesClient() as client:
        resp = client.delete_forest(forest="aaa", level="full")

    assert resp.status_code == 204
    assert not resp.text


@responses.activate()
def test_get_forest_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-forest-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(
        "http://localhost:8002/manage/v2/forests/Documents/properties",
    )
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_forest_properties(forest="Documents", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["forest-name"] == "Documents"


@responses.activate()
def test_put_forest_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-forest-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(
        "http://localhost:8002/manage/v2/forests/non-existing-forest/properties",
    )
    builder.with_request_content_type("application/json")
    builder.with_request_body({"forest-name": "custom-forest"})
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_put()

    with MLResourcesClient() as client:
        resp = client.put_forest_properties(
            forest="non-existing-forest",
            body={"forest-name": "custom-forest"},
        )

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHFOREST"


@responses.activate()
def test_get_roles():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-roles.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/roles")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_roles(data_format="json")

    expected_uri = "/manage/v2/roles?view=default"
    assert resp.status_code == 200
    assert resp.json()["role-default-list"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_post_roles():
    body = '<role-properties xmlns="http://marklogic.com/manage/role/properties" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-roles.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/roles")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(400)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.post_roles(body=body)

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values." in resp.text


@responses.activate()
def test_get_role():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-role.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/roles/admin")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_role(role="admin", data_format="json")

    expected_uri = "/manage/v2/roles/admin?view=default"
    assert resp.status_code == 200
    assert resp.json()["role-default"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_delete_role():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/roles/custom-role")
    builder.with_response_status(204)
    builder.with_empty_response_body()
    builder.build_delete()

    with MLResourcesClient() as client:
        resp = client.delete_role(role="custom-role")

    assert resp.status_code == 204
    assert not resp.text


@responses.activate()
def test_get_role_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-role-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/roles/admin/properties")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_role_properties(role="admin", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["role-name"] == "admin"


@responses.activate()
def test_put_role_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-role-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(
        "http://localhost:8002/manage/v2/roles/non-existing-role/properties",
    )
    builder.with_request_content_type("application/json")
    builder.with_request_body({"role-name": "custom-db"})
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(400)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_put()

    with MLResourcesClient() as client:
        resp = client.put_role_properties(
            role="non-existing-role",
            body={"role-name": "custom-db"},
        )

    assert resp.status_code == 400
    assert (
        "Payload has errors in structure, content-type or values. "
        "Role non-existing-role does not exist or is not accessible"
    ) in resp.text


@responses.activate()
def test_get_users():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-users.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/users")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_users(data_format="json")

    expected_uri = "/manage/v2/users?view=default"
    assert resp.status_code == 200
    assert resp.json()["user-default-list"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_post_users():
    body = '<user-properties xmlns="http://marklogic.com/manage/user/properties" />'

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-users.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/users")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(400)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.post_users(body=body)

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values." in resp.text


@responses.activate()
def test_get_user():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-user.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/users/admin")
    builder.with_request_param("format", "json")
    builder.with_request_param("view", "default")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_user(user="admin", data_format="json")

    expected_uri = "/manage/v2/users/admin?view=default"
    assert resp.status_code == 200
    assert resp.json()["user-default"]["meta"]["uri"] == expected_uri


@responses.activate()
def test_delete_user():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-delete-user.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/users/custom-user")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    with MLResourcesClient() as client:
        resp = client.delete_user(user="custom-user")

    assert resp.status_code == 404
    assert "User does not exist: custom-user" in resp.text


@responses.activate()
def test_get_user_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-user-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/users/admin/properties")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_user_properties(user="admin", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["user-name"] == "admin"


@responses.activate()
def test_put_user_properties():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-put-user-properties.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(
        "http://localhost:8002/manage/v2/users/non-existing-user/properties",
    )
    builder.with_request_content_type("application/json")
    builder.with_request_body({"user-name": "custom-db"})
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_put()

    with MLResourcesClient() as client:
        resp = client.put_user_properties(
            user="non-existing-user",
            body={"user-name": "custom-db"},
        )

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "SEC-USERDNE"


@responses.activate()
def test_get_documents():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-documents.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/path/to/non-existing/document.xml")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()

    with MLResourcesClient() as client:
        resp = client.get_documents(
            uri="/path/to/non-existing/document.xml",
            data_format="json",
        )

    assert resp.status_code == 500
    assert resp.json()["errorResponse"]["messageCode"] == "RESTAPI-NODOCUMENT"


@responses.activate()
def test_post_documents():
    body_part = {
        "content-type": "application/json",
        "content-disposition": "inline",
        "content": {"root": "data"},
    }

    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-post-documents.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(500)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_post()

    with MLResourcesClient() as client:
        resp = client.post_documents(body_parts=[DocumentsBodyPart(**body_part)])

    assert resp.status_code == 500
    assert resp.json() == {
        "errorResponse": {
            "statusCode": "500",
            "status": "Internal Server Error",
            "messageCode": "XDMP-AS",
            "message": "XDMP-AS: (err:XPTY0004) $uri as xs:string -- "
            "Invalid coercion: () as xs:string",
        },
    }


@responses.activate()
def test_delete_documents():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-delete-documents.xml",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/documents")
    builder.with_request_param("uri", "/path/to/non-existing/document.xml")
    builder.with_request_param("result", "wiped")
    builder.with_response_content_type("application/xml; charset=UTF-8")
    builder.with_response_status(400)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_delete()

    with MLResourcesClient() as client:
        resp = client.delete_documents(
            uri="/path/to/non-existing/document.xml",
            wipe_temporal=True,
        )

    assert resp.status_code == 400
    assert (
        "Endpoint does not support query parameter: "
        "invalid parameters: result "
        "for /path/to/non-existing/document.xml"
    ) in resp.text
