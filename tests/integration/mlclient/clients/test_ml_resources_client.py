from __future__ import annotations

import datetime
from time import sleep
from typing import ClassVar

import pytest
from requests import Response

from mlclient import MLResourcesClient, MLResponseParser
from mlclient.calls.model import DocumentsBodyPart


class TestEvalEndpoint:
    @pytest.mark.ml_access()
    def test_eval(
        self,
    ):
        parsed_resp = self._eval_xquery(
            code="xquery version '1.0-ml'; "
            "declare variable $element as element() external; "
            "<new-parent>{$element/child::element()}</new-parent>",
            variables={
                "element": "<parent><child/></parent>",
            },
        )
        assert parsed_resp == "<new-parent><child/></new-parent>"

    @classmethod
    def _eval_xquery(
        cls,
        code: str,
        variables: dict,
    ) -> str | list[str]:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.eval(
                xquery=code,
                variables=variables,
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return MLResponseParser.parse(resp, str)


class TestLogsEndpoint:
    @pytest.mark.ml_access()
    def test_get_logs(
        self,
    ):
        self._produce_test_logs()
        eval_logs_count = self._test_error_logs()
        self._test_access_logs(eval_logs_count)
        self._test_request_logs()

    @classmethod
    def _produce_test_logs(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            for i in range(1, 11):
                client.eval(xquery=f'xdmp:log("Test Log {i}", "error")')
        sleep(1)

    @classmethod
    def _test_error_logs(
        cls,
    ) -> int:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_logs(
                filename=f"{client.port}_ErrorLog.txt",
                data_format="json",
                start_time=str(datetime.date.today()),
                regex="Test Log .{1,2}",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        logfile = resp.json()["logfile"]
        logs_count = len(logfile["log"])
        assert logs_count % 10 == 0

        return logs_count

    @classmethod
    def _test_access_logs(
        cls,
        eval_logs_count: int,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_logs(
                filename=f"{client.port}_AccessLog.txt",
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        logfile = resp.json()["logfile"]
        assert isinstance(logfile["message"], str)

        logs = logfile["message"].split("\n")
        eval_logs = [
            log
            for log in logs
            if '"POST /v1/eval HTTP/1.1"' in log and "python-requests" in log
        ]
        assert len(eval_logs) >= eval_logs_count

    @classmethod
    def _test_request_logs(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_logs(
                filename=f"{client.port}_RequestLog.txt",
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        logfile = resp.json()["logfile"]
        assert isinstance(logfile["message"], str)


class TestDatabasesManagement:
    TEST_DATABASE_CONFIG: ClassVar[dict] = {"database-name": "TestDB"}

    @pytest.mark.ml_access()
    def test_db_management(
        self,
    ):
        init_count = -1
        try:
            init_count = self._init_check()

            self._create_database()
            self._middle_check(init_count)

            self._check_database_config()
            self._update_database_properties()
            self._check_database_properties()

            self._perform_action_on_database()
        finally:
            self._delete_database()
            self._final_check(init_count)

    @classmethod
    def _init_check(
        cls,
    ) -> int:
        resp = cls._get_databases()

        data = resp.json()["database-default-list"]["list-items"]
        databases = data["list-item"]
        databases_names = [database["nameref"] for database in databases]
        assert cls.TEST_DATABASE_CONFIG["database-name"] not in databases_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_databases()

        data = resp.json()["database-default-list"]["list-items"]
        databases = data["list-item"]
        databases_names = [database["nameref"] for database in databases]
        assert cls.TEST_DATABASE_CONFIG["database-name"] in databases_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_databases()

        data = resp.json()["database-default-list"]["list-items"]
        databases = data["list-item"]
        databases_names = [database["nameref"] for database in databases]
        assert cls.TEST_DATABASE_CONFIG["database-name"] not in databases_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_database_config(
        cls,
    ):
        resp = cls._get_database(
            cls.TEST_DATABASE_CONFIG["database-name"],
            view="config",
        )
        database_config = resp.json()["database-config"]["config-properties"]
        assert database_config["language"] == "en"
        assert database_config["enabled"] is True

    @classmethod
    def _update_database_properties(
        cls,
    ):
        cls._put_database_properties(
            cls.TEST_DATABASE_CONFIG["database-name"],
            {"enabled": False},
        )

    @classmethod
    def _check_database_properties(
        cls,
    ):
        resp = cls._get_database_properties(
            cls.TEST_DATABASE_CONFIG["database-name"],
        )
        database_props = resp.json()
        assert database_props["language"] == "en"
        assert database_props["enabled"] is False

    @classmethod
    def _get_databases(
        cls,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_databases(data_format="json")
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_database(
        cls,
        database: str,
        view: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_database(database=database, data_format="json", view=view)
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_database_properties(
        cls,
        database: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_database_properties(database=database, data_format="json")
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _put_database_properties(
        cls,
        database: str,
        body: dict,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.put_database_properties(
                database=database,
                body=body,
            )
        assert resp.status_code == 204
        assert resp.reason == "No Content"

        return resp

    @classmethod
    def _create_database(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_databases(cls.TEST_DATABASE_CONFIG)
        assert resp.status_code == 201
        assert resp.reason == "Created"

    @classmethod
    def _delete_database(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.delete_database(cls.TEST_DATABASE_CONFIG["database-name"])
        assert resp.status_code == 204
        assert resp.reason == "No Content"

    @classmethod
    def _perform_action_on_database(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_database(
                database=cls.TEST_DATABASE_CONFIG["database-name"],
                body={"operation": "clear-database"},
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"


class TestServersManagement:
    TEST_SERVER_CONFIG: ClassVar[dict] = {
        "server-name": "TestServer",
        "root": "/",
        "port": 8100,
        "content-database": "Documents",
    }

    def test_servers_management(
        self,
    ):
        init_count = -1
        try:
            init_count = self._init_check()
            self._create_server()
            self._middle_check(init_count)

            self._check_server_config()
            self._update_server_properties()
            self._check_server_properties()
        finally:
            self._delete_server()
            self._final_check(init_count)

    @classmethod
    def _init_check(
        cls,
    ) -> int:
        resp = cls._get_servers()

        data = resp.json()["server-default-list"]["list-items"]
        servers = data["list-item"]
        servers_names = [database["nameref"] for database in servers]
        assert cls.TEST_SERVER_CONFIG["server-name"] not in servers_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_servers()

        data = resp.json()["server-default-list"]["list-items"]
        servers = data["list-item"]
        servers_names = [database["nameref"] for database in servers]
        assert cls.TEST_SERVER_CONFIG["server-name"] in servers_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_servers()

        data = resp.json()["server-default-list"]["list-items"]
        servers = data["list-item"]
        servers_names = [database["nameref"] for database in servers]
        assert cls.TEST_SERVER_CONFIG["server-name"] not in servers_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_server_config(
        cls,
    ):
        resp = cls._get_server(
            cls.TEST_SERVER_CONFIG["server-name"],
            view="config",
        )
        server_config = resp.json()["http-server-config"]["http-config-properties"]
        assert server_config["root"] == cls.TEST_SERVER_CONFIG["root"]
        assert server_config["port"] == cls.TEST_SERVER_CONFIG["port"]
        assert server_config["enabled"] is True

    @classmethod
    def _update_server_properties(
        cls,
    ):
        cls._put_server_properties(
            cls.TEST_SERVER_CONFIG["server-name"],
            {"enabled": False},
        )

    @classmethod
    def _check_server_properties(
        cls,
    ):
        resp = cls._get_server_properties(
            cls.TEST_SERVER_CONFIG["server-name"],
        )
        server_props = resp.json()
        assert server_props["root"] == cls.TEST_SERVER_CONFIG["root"]
        assert server_props["port"] == cls.TEST_SERVER_CONFIG["port"]
        assert server_props["enabled"] is False

    @classmethod
    def _get_servers(
        cls,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_servers(data_format="json")
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_server(
        cls,
        server: str,
        view: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_server(
                server=server,
                group_id="Default",
                data_format="json",
                view=view,
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_server_properties(
        cls,
        server: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_server_properties(
                server=server,
                group_id="Default",
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _put_server_properties(
        cls,
        server: str,
        body: dict,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.put_server_properties(
                server=server,
                group_id="Default",
                body=body,
            )
        assert resp.status_code == 204
        assert resp.reason == "No Content"

        return resp

    @classmethod
    def _create_server(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_servers(
                group_id="Default",
                server_type="http",
                body=cls.TEST_SERVER_CONFIG,
            )
        assert resp.status_code == 201
        assert resp.reason == "Created"

    @classmethod
    def _delete_server(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.delete_server(
                server=cls.TEST_SERVER_CONFIG["server-name"],
                group_id="Default",
            )
        assert resp.status_code == 202
        assert resp.reason == "Accepted"


@pytest.mark.ml_access()
def test_get_forests():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_forests(data_format="json", database="Documents")

    expected_uri = "/manage/v2/forests?view=default&database-id=Documents"
    assert resp.status_code == 200
    assert resp.json()["forest-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access()
def test_post_forests():
    body = '<forest-create xmlns="http://marklogic.com/manage" />'
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.post_forests(body=body)

    assert resp.status_code == 500


@pytest.mark.ml_access()
def test_put_forests():
    body = '<forest-migrate xmlns="http://marklogic.com/manage" />'
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.put_forests(body=body)

    assert resp.status_code == 400
    assert (
        "Payload has errors in structure, content-type or values. "
        "Cannot validate payload, no forests specified."
    ) in resp.text


@pytest.mark.ml_access()
def test_get_forest():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_forest(forest="Documents", data_format="json")

    expected_uri = "/manage/v2/forests/Documents?view=default"
    assert resp.status_code == 200
    assert resp.json()["forest-default"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access()
def test_post_forest():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.post_forest(forest="aaa", body={"state": "clear"})

    assert resp.status_code == 404
    assert "XDMP-NOSUCHFOREST" in resp.text


@pytest.mark.ml_access()
def test_delete_forest():
    with MLResourcesClient(auth_method="digest") as client:
        client.post_forests(body={"forest-name": "aaa"})
        resp = client.delete_forest(forest="aaa", level="full")

    assert resp.status_code == 204
    assert not resp.text


@pytest.mark.ml_access()
def test_get_forest_properties():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_forest_properties(forest="Documents", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["forest-name"] == "Documents"


@pytest.mark.ml_access()
def test_put_forest_properties():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.put_forest_properties(
            forest="non-existing-forest",
            body={"forest-name": "custom-forest"},
        )

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "XDMP-NOSUCHFOREST"


@pytest.mark.ml_access()
def test_get_roles():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_roles(data_format="json")

    expected_uri = "/manage/v2/roles?view=default"
    assert resp.status_code == 200
    assert resp.json()["role-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access()
def test_post_roles():
    body = '<role-properties xmlns="http://marklogic.com/manage/role/properties" />'
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.post_roles(body=body)

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values." in resp.text


@pytest.mark.ml_access()
def test_get_role():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_role(role="admin", data_format="json")

    expected_uri = "/manage/v2/roles/admin?view=default"
    assert resp.status_code == 200
    assert resp.json()["role-default"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access()
def test_delete_role():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.delete_role(role="custom-role")

    assert resp.status_code == 204
    assert not resp.text


@pytest.mark.ml_access()
def test_get_role_properties():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_role_properties(role="admin", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["role-name"] == "admin"


@pytest.mark.ml_access()
def test_put_role_properties():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.put_role_properties(
            role="non-existing-role",
            body={"role-name": "custom-db"},
        )

    assert resp.status_code == 400
    assert (
        "Payload has errors in structure, content-type or values. "
        "Role non-existing-role does not exist or is not accessible"
    ) in resp.text


@pytest.mark.ml_access()
def test_get_users():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_users(data_format="json")

    expected_uri = "/manage/v2/users?view=default"
    assert resp.status_code == 200
    assert resp.json()["user-default-list"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access()
def test_post_users():
    body = '<user-properties xmlns="http://marklogic.com/manage/user/properties" />'
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.post_users(body=body)

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values." in resp.text


@pytest.mark.ml_access()
def test_get_user():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_user(user="admin", data_format="json")

    expected_uri = "/manage/v2/users/admin?view=default"
    assert resp.status_code == 200
    assert resp.json()["user-default"]["meta"]["uri"] == expected_uri


@pytest.mark.ml_access()
def test_delete_user():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.delete_user(user="custom-user")

    assert resp.status_code == 404
    assert "User does not exist: custom-user" in resp.text


@pytest.mark.ml_access()
def test_get_user_properties():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_user_properties(user="admin", data_format="json")

    assert resp.status_code == 200
    assert resp.json()["user-name"] == "admin"


@pytest.mark.ml_access()
def test_put_user_properties():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.put_user_properties(
            user="non-existing-user",
            body={"user-name": "custom-db"},
        )

    assert resp.status_code == 404
    assert resp.json()["errorResponse"]["messageCode"] == "SEC-USERDNE"


@pytest.mark.ml_access()
def test_get_documents():
    with MLResourcesClient(auth_method="digest") as client:
        resp = client.get_documents(
            uri="/path/to/non-existing/document.xml",
            data_format="json",
        )

    assert resp.status_code == 500
    assert resp.json()["errorResponse"]["messageCode"] == "RESTAPI-NODOCUMENT"


@pytest.mark.ml_access()
def test_post_documents():
    body_part = {
        "content-type": "application/json",
        "content-disposition": "inline",
        "content": {"root": "data"},
    }
    with MLResourcesClient(auth_method="digest") as client:
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


@pytest.mark.ml_access()
def test_delete_documents():
    with MLResourcesClient(auth_method="digest") as client:
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
