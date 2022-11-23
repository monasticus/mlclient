import pytest

from mlclient import MLResourceClient
from mlclient.calls import EvalCall


@pytest.fixture
def xquery():
    return """xquery version '1.0-ml';
    
    declare variable $element as element() external;
    
    <new-parent>{$element/child::element()}</new-parent>
    """


@pytest.mark.ml_access
def test_call(xquery):
    eval_call = EvalCall(xquery=xquery, variables={"element": "<parent><child/></parent>"})
    with MLResourceClient(auth_method="digest") as client:
        resp = client.call(eval_call)

    assert resp.status_code == 200
    assert "<new-parent><child/></new-parent>" in resp.text


@pytest.mark.ml_access
def test_eval(xquery):
    with MLResourceClient(auth_method="digest") as client:
        resp = client.eval(xquery=xquery, variables={"element": "<parent><child/></parent>"})

    assert resp.status_code == 200
    assert "<new-parent><child/></new-parent>" in resp.text


@pytest.mark.ml_access
def test_get_logs():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_logs(filename="ErrorLog.txt", data_format="json")

    assert resp.status_code == 200
    assert "logfile" in resp.json()


@pytest.mark.ml_access
def test_get_databases():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_databases(data_format="json")

    expected_uri = "/manage/v2/databases?view=default"
    assert resp.status_code == 200
    assert resp.json()["database-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access
def test_post_databases():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.post_databases(body='<database-properties xmlns="http://marklogic.com/manage" />')

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values. Database name missing." in resp.text


@pytest.mark.ml_access
def test_get_database():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_database(database="Documents", data_format="json")

    expected_uri = "/manage/v2/databases/Documents?view=default"
    assert resp.status_code == 200
    assert resp.json()["database-default"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access
def test_post_database():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.post_database(database="Documents", body={"operation": "clear-database"})

    assert resp.status_code == 200
    assert not resp.text


@pytest.mark.ml_access
def test_delete_database():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.delete_database(database="custom-db")

    assert resp.status_code == 204
    assert not resp.text


@pytest.mark.ml_access
def test_get_database_properties():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_database_properties(database="Documents", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["database-name"] == "Documents"


@pytest.mark.ml_access
def test_put_database_properties():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.put_database_properties(database="non-existing-db", body={"database-name": "custom-db"})

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHDB"


@pytest.mark.ml_access
def test_get_servers():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_servers(data_format="json")

    expected_uri = "/manage/v2/servers?view=default"
    assert resp.status_code == 200
    assert resp.json()["server-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access
def test_post_servers():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.post_servers(group_id="Default",
                                   server_type="http",
                                   body='<http-server-properties xmlns="http://marklogic.com/manage" />')

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values. Server name missing." in resp.text


@pytest.mark.ml_access
def test_get_server():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_server(server="App-Services", group_id="Default", data_format="json")

    expected_uri = "/manage/v2/servers/App-Services?group-id=Default&view=default"
    assert resp.status_code == 200
    assert resp.json()["server-default"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access
def test_delete_server():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.delete_server(server="Non-existing-server",
                                    group_id="Non-existing-group")

    assert resp.status_code == 404
    assert "No such group Non-existing-group" in resp.text


@pytest.mark.ml_access
def test_get_server_properties():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_server_properties(server="App-Services", group_id="Default", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["server-name"] == "App-Services"


@pytest.mark.ml_access
def test_put_server_properties():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.put_server_properties(server="non-existing-server",
                                            group_id="non-existing-group",
                                            body={"server-name": "non-existing-server"})

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHGROUP"


@pytest.mark.ml_access
def test_get_forests():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_forests(data_format="json", database="Documents")

    expected_uri = "/manage/v2/forests?view=default&database-id=Documents"
    assert resp.status_code == 200
    assert resp.json()["forest-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access
def test_post_forests():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.post_forests(body='<forest-create xmlns="http://marklogic.com/manage" />')

    assert resp.status_code == 500


@pytest.mark.ml_access
def test_put_forests():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.put_forests(body='<forest-migrate xmlns="http://marklogic.com/manage" />')

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values. " \
           "Cannot validate payload, no forests specified." in resp.text


@pytest.mark.ml_access
def test_get_forest():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_forest(forest="Documents", data_format="json")

    expected_uri = "/manage/v2/forests/Documents?view=default"
    assert resp.status_code == 200
    assert resp.json()["forest-default"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access
def test_post_forest():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.post_forest(forest="aaa", body={"state": "clear"})

    assert resp.status_code == 404
    assert "XDMP-NOSUCHFOREST" in resp.text


@pytest.mark.ml_access
def test_delete_forest():
    with MLResourceClient(auth_method="digest") as client:
        client.post_forests(body={"forest-name": "aaa"})
        resp = client.delete_forest(forest="aaa", level="full")

    assert resp.status_code == 204
    assert not resp.text


@pytest.mark.ml_access
def test_get_forest_properties():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_forest_properties(forest="Documents", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["forest-name"] == "Documents"


@pytest.mark.ml_access
def test_put_forest_properties():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.put_forest_properties(forest="non-existing-forest", body={"forest-name": "custom-forest"})

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHFOREST"


@pytest.mark.ml_access
def test_get_roles():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_roles(data_format="json")

    expected_uri = "/manage/v2/roles?view=default"
    assert resp.status_code == 200
    assert resp.json()["role-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access
def test_post_roles():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.post_databases(body='<role-properties xmlns="http://marklogic.com/manage/role/properties" />')

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values." in resp.text


@pytest.mark.ml_access
def test_get_role():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_role(role="admin", data_format="json")

    expected_uri = "/manage/v2/roles/admin?view=default"
    assert resp.status_code == 200
    assert resp.json()["role-default"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access
def test_delete_role():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.delete_role(role="custom-role")

    assert resp.status_code == 204
    assert not resp.text


@pytest.mark.ml_access
def test_get_role_properties():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_role_properties(role="admin", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["role-name"] == "admin"


@pytest.mark.ml_access
def test_put_role_properties():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.put_role_properties(role="non-existing-role", body={"role-name": "custom-db"})

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values. " \
           "Role non-existing-role does not exist or is not accessible" in resp.text
