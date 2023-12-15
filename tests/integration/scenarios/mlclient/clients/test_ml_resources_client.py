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

    @classmethod
    def _test_error_logs(
        cls,
    ) -> int:
        sleep(1)
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
        sleep(1)
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_logs(
                filename=f"{client.port}_RequestLog.txt",
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        logfile = resp.json()["logfile"]
        assert isinstance(logfile.get("message"), str) or len(logfile) == 6


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


class TestForestsManagement:
    TEST_FOREST_CONFIG: ClassVar[dict] = {"forest-name": "test-forest-1"}

    @pytest.mark.ml_access()
    def test_forest_management(
        self,
    ):
        init_count = -1
        try:
            init_count = self._init_check()

            self._create_forest()
            self._middle_check(init_count)

            self._check_forest_config()
            self._update_forest_properties()
            self._check_forest_properties()

            self._initiate_state_change_on_forest()
            self._perform_action_on_forests()
        finally:
            self._delete_forest()
            self._final_check(init_count)

    @classmethod
    def _init_check(
        cls,
    ) -> int:
        resp = cls._get_forests()

        data = resp.json()["forest-default-list"]["list-items"]
        forests = data["list-item"]
        forests_names = [forest["nameref"] for forest in forests]
        assert cls.TEST_FOREST_CONFIG["forest-name"] not in forests_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_forests()

        data = resp.json()["forest-default-list"]["list-items"]
        forests = data["list-item"]
        forests_names = [forest["nameref"] for forest in forests]
        assert cls.TEST_FOREST_CONFIG["forest-name"] in forests_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_forests()

        data = resp.json()["forest-default-list"]["list-items"]
        forests = data["list-item"]
        forests_names = [forest["nameref"] for forest in forests]
        assert cls.TEST_FOREST_CONFIG["forest-name"] not in forests_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_forest_config(
        cls,
    ):
        resp = cls._get_forest(
            cls.TEST_FOREST_CONFIG["forest-name"],
            view="config",
        )
        forest_config = resp.json()["forest-config"]["config-properties"]
        assert forest_config["enabled"] is True
        assert forest_config["rebalancer-enable"] is True

    @classmethod
    def _update_forest_properties(
        cls,
    ):
        cls._put_forest_properties(
            cls.TEST_FOREST_CONFIG["forest-name"],
            {"rebalancer-enable": False},
        )

    @classmethod
    def _check_forest_properties(
        cls,
    ):
        resp = cls._get_forest_properties(
            cls.TEST_FOREST_CONFIG["forest-name"],
        )
        forest_props = resp.json()
        assert forest_props["enabled"] is True
        assert forest_props["rebalancer-enable"] is False

    @classmethod
    def _get_forests(
        cls,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_forests(data_format="json")
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_forest(
        cls,
        forest: str,
        view: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_forest(forest=forest, data_format="json", view=view)
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_forest_properties(
        cls,
        forest: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_forest_properties(forest=forest, data_format="json")
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _put_forest_properties(
        cls,
        forest: str,
        body: dict,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.put_forest_properties(
                forest=forest,
                body=body,
            )
        assert resp.status_code == 204
        assert resp.reason == "No Content"

        return resp

    @classmethod
    def _create_forest(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_forests(cls.TEST_FOREST_CONFIG)
        assert resp.status_code == 201
        assert resp.reason == "Created"

    @classmethod
    def _delete_forest(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.delete_forest(
                cls.TEST_FOREST_CONFIG["forest-name"],
                level="full",
            )
        assert resp.status_code == 204
        assert resp.reason == "No Content"

    @classmethod
    def _initiate_state_change_on_forest(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_forest(
                forest=cls.TEST_FOREST_CONFIG["forest-name"],
                body={"state": "clear"},
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

    @classmethod
    def _perform_action_on_forests(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.put_forests(
                body={
                    "operation": "forest-migrate",
                },
            )
        assert resp.status_code == 400
        assert resp.reason == "Bad Request"
        err = resp.json()["errorResponse"]
        assert err["messageCode"] == "MANAGE-INVALIDPAYLOAD"
        assert err["message"] == (
            "MANAGE-INVALIDPAYLOAD: (err:FOER0000) "
            "Payload has errors in structure, content-type or values. "
            "Cannot validate payload, no forests specified."
        )


class TestRolesManagement:
    TEST_ROLE_CONFIG: ClassVar[dict] = {
        "role-name": "test-role",
        "description": "A test role",
    }

    def test_roles_management(
        self,
    ):
        init_count = -1
        try:
            init_count = self._init_check()
            self._create_role()
            self._middle_check(init_count)

            self._check_role_config()
            self._update_role_properties()
            self._check_role_properties()
        finally:
            self._delete_role()
            self._final_check(init_count)

    @classmethod
    def _init_check(
        cls,
    ) -> int:
        resp = cls._get_roles()

        data = resp.json()["role-default-list"]["list-items"]
        roles = data["list-item"]
        roles_names = [role["nameref"] for role in roles]
        assert cls.TEST_ROLE_CONFIG["role-name"] not in roles_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_roles()

        data = resp.json()["role-default-list"]["list-items"]
        roles = data["list-item"]
        roles_names = [role["nameref"] for role in roles]
        assert cls.TEST_ROLE_CONFIG["role-name"] in roles_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_roles()

        data = resp.json()["role-default-list"]["list-items"]
        roles = data["list-item"]
        roles_names = [role["nameref"] for role in roles]
        assert cls.TEST_ROLE_CONFIG["role-name"] not in roles_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_role_config(
        cls,
    ):
        resp = cls._get_role(
            cls.TEST_ROLE_CONFIG["role-name"],
        )
        role_config = resp.json()["role-default"]
        assert role_config["name"] == cls.TEST_ROLE_CONFIG["role-name"]
        assert role_config["description"] == cls.TEST_ROLE_CONFIG["description"]

    @classmethod
    def _update_role_properties(
        cls,
    ):
        cls._put_role_properties(
            cls.TEST_ROLE_CONFIG["role-name"],
            {"description": cls.TEST_ROLE_CONFIG["description"].upper()},
        )

    @classmethod
    def _check_role_properties(
        cls,
    ):
        resp = cls._get_role_properties(
            cls.TEST_ROLE_CONFIG["role-name"],
        )
        role_config = resp.json()
        assert role_config["role-name"] == cls.TEST_ROLE_CONFIG["role-name"]
        assert role_config["description"] == cls.TEST_ROLE_CONFIG["description"].upper()

    @classmethod
    def _get_roles(
        cls,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_roles(data_format="json")
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_role(
        cls,
        role: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_role(
                role=role,
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_role_properties(
        cls,
        role: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_role_properties(
                role=role,
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _put_role_properties(
        cls,
        role: str,
        body: dict,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.put_role_properties(
                role=role,
                body=body,
            )
        assert resp.status_code == 204
        assert resp.reason == "No Content"

        return resp

    @classmethod
    def _create_role(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_roles(
                body=cls.TEST_ROLE_CONFIG,
            )
        assert resp.status_code == 201
        assert resp.reason == "Created"

    @classmethod
    def _delete_role(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.delete_role(
                role=cls.TEST_ROLE_CONFIG["role-name"],
            )
        assert resp.status_code == 204
        assert resp.reason == "No Content"


class TestUsersManagement:
    TEST_USER_CONFIG: ClassVar[dict] = {
        "user-name": "test-user",
        "description": "A test user",
    }

    def test_users_management(
        self,
    ):
        init_count = -1
        try:
            init_count = self._init_check()
            self._create_user()
            self._middle_check(init_count)

            self._check_user_config()
            self._update_user_properties()
            self._check_user_properties()
        finally:
            self._delete_user()
            self._final_check(init_count)

    @classmethod
    def _init_check(
        cls,
    ) -> int:
        resp = cls._get_users()

        data = resp.json()["user-default-list"]["list-items"]
        users = data["list-item"]
        users_names = [user["nameref"] for user in users]
        assert cls.TEST_USER_CONFIG["user-name"] not in users_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_users()

        data = resp.json()["user-default-list"]["list-items"]
        users = data["list-item"]
        users_names = [user["nameref"] for user in users]
        assert cls.TEST_USER_CONFIG["user-name"] in users_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        init_count: int,
    ):
        resp = cls._get_users()

        data = resp.json()["user-default-list"]["list-items"]
        users = data["list-item"]
        users_names = [user["nameref"] for user in users]
        assert cls.TEST_USER_CONFIG["user-name"] not in users_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_user_config(
        cls,
    ):
        resp = cls._get_user(
            cls.TEST_USER_CONFIG["user-name"],
        )
        user_config = resp.json()["user-default"]
        assert user_config["name"] == cls.TEST_USER_CONFIG["user-name"]
        assert user_config["description"] == cls.TEST_USER_CONFIG["description"]

    @classmethod
    def _update_user_properties(
        cls,
    ):
        cls._put_user_properties(
            cls.TEST_USER_CONFIG["user-name"],
            {"description": cls.TEST_USER_CONFIG["description"].upper()},
        )

    @classmethod
    def _check_user_properties(
        cls,
    ):
        resp = cls._get_user_properties(
            cls.TEST_USER_CONFIG["user-name"],
        )
        user_config = resp.json()
        assert user_config["user-name"] == cls.TEST_USER_CONFIG["user-name"]
        assert user_config["description"] == cls.TEST_USER_CONFIG["description"].upper()

    @classmethod
    def _get_users(
        cls,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_users(data_format="json")
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_user(
        cls,
        user: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_user(
                user=user,
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _get_user_properties(
        cls,
        user: str,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_user_properties(
                user=user,
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        return resp

    @classmethod
    def _put_user_properties(
        cls,
        user: str,
        body: dict,
    ) -> Response:
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.put_user_properties(
                user=user,
                body=body,
            )
        assert resp.status_code == 204
        assert resp.reason == "No Content"

        return resp

    @classmethod
    def _create_user(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_users(
                body=cls.TEST_USER_CONFIG,
            )
        assert resp.status_code == 201
        assert resp.reason == "Created"

    @classmethod
    def _delete_user(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.delete_user(
                user=cls.TEST_USER_CONFIG["user-name"],
            )
        assert resp.status_code == 204
        assert resp.reason == "No Content"


class TestDocumentsManagement:
    DOCUMENT_BODY_PART_1 = DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": {
                "body_part_type": "attachment",
                "filename": "/some/dir/doc1.json",
            },
            "content": b'{"root": {"child": "data"}}',
        },
    )
    DOCUMENT_BODY_PART_2 = DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": {
                "body_part_type": "attachment",
                "filename": "/some/dir/doc1.json",
            },
            "content": b'{"root2": {"child2": "data2"}}',
        },
    )

    def test_docs_management(
        self,
    ):
        try:
            self._check_does_not_exist()

            self._create_document()
            self._check_created()

            self._update_document()
            self._check_updated()
        finally:
            self._delete_document()
            self._check_does_not_exist()

    @classmethod
    def _check_does_not_exist(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_documents(
                uri=cls.DOCUMENT_BODY_PART_1.content_disposition.filename,
                data_format="json",
            )
        assert resp.status_code == 500
        assert resp.reason == "Internal Server Error"
        assert resp.json()["errorResponse"]["messageCode"] == "RESTAPI-NODOCUMENT"

    @classmethod
    def _check_created(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_documents(
                uri=cls.DOCUMENT_BODY_PART_1.content_disposition.filename,
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        parsed_resp = MLResponseParser.parse(resp)
        assert parsed_resp == {"root": {"child": "data"}}

    @classmethod
    def _check_updated(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.get_documents(
                uri=cls.DOCUMENT_BODY_PART_1.content_disposition.filename,
                data_format="json",
            )
        assert resp.status_code == 200
        assert resp.reason == "OK"

        parsed_resp = MLResponseParser.parse(resp)
        assert parsed_resp == {"root2": {"child2": "data2"}}

    @classmethod
    def _create_document(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_documents(body_parts=[cls.DOCUMENT_BODY_PART_1])
            assert resp.status_code == 200
            assert resp.reason == "Bulk Change Written"

    @classmethod
    def _update_document(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.post_documents(body_parts=[cls.DOCUMENT_BODY_PART_2])
            assert resp.status_code == 200
            assert resp.reason == "Bulk Change Written"

    @classmethod
    def _delete_document(
        cls,
    ):
        with MLResourcesClient(auth_method="digest") as client:
            resp = client.delete_documents(
                uri=cls.DOCUMENT_BODY_PART_1.content_disposition.filename,
            )
            assert resp.status_code == 204
            assert resp.reason == "Content Deleted"
