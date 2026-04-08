from __future__ import annotations

from typing import ClassVar

import httpx
import pytest
from httpx import Response
from pytest_bdd import scenarios

from mlclient import MLClient, MLResponseParser
from mlclient.models.http import DocumentsBodyPart as BodyPart

scenarios("../../../features/mlclient/clients/api_wrappers.feature")

pytest_plugins = [
    "tests.integration.steps.client_steps",
    "tests.integration.steps.responses",
    "tests.integration.steps.setup",
]


@pytest.fixture(scope="class")
def ml_client():
    with MLClient(
        auth_method="digest",
    ) as ml:
        yield ml


class TestDatabasesManagement:
    TEST_DATABASE_CONFIG: ClassVar[dict] = {"database-name": "TestDB"}

    @pytest.mark.ml_access
    def test_db_management(
        self,
        ml_client: MLClient,
    ):
        init_count = -1
        try:
            init_count = self._init_check(ml_client)

            self._create_database(ml_client)
            self._middle_check(ml_client, init_count)

            self._check_database_config(ml_client)
            self._update_database_properties(ml_client)
            self._check_database_properties(ml_client)

            self._perform_action_on_database(ml_client)
        finally:
            self._delete_database(ml_client)
            self._final_check(ml_client, init_count)

    @classmethod
    def _init_check(
        cls,
        ml: MLClient,
    ) -> int:
        resp = cls._get_databases(ml)

        data = resp.json()["database-default-list"]["list-items"]
        databases = data["list-item"]
        databases_names = [database["nameref"] for database in databases]
        assert cls.TEST_DATABASE_CONFIG["database-name"] not in databases_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_databases(ml)

        data = resp.json()["database-default-list"]["list-items"]
        databases = data["list-item"]
        databases_names = [database["nameref"] for database in databases]
        assert cls.TEST_DATABASE_CONFIG["database-name"] in databases_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_databases(ml)

        data = resp.json()["database-default-list"]["list-items"]
        databases = data["list-item"]
        databases_names = [database["nameref"] for database in databases]
        assert cls.TEST_DATABASE_CONFIG["database-name"] not in databases_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_database_config(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_database(
            ml,
            cls.TEST_DATABASE_CONFIG["database-name"],
            view="config",
        )
        database_config = resp.json()["database-config"]["config-properties"]
        assert database_config["language"] == "en"
        assert database_config["enabled"] is True

    @classmethod
    def _update_database_properties(
        cls,
        ml: MLClient,
    ):
        cls._put_database_properties(
            ml,
            cls.TEST_DATABASE_CONFIG["database-name"],
            {"enabled": False},
        )

    @classmethod
    def _check_database_properties(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_database_properties(
            ml,
            cls.TEST_DATABASE_CONFIG["database-name"],
        )
        database_props = resp.json()
        assert database_props["language"] == "en"
        assert database_props["enabled"] is False

    @classmethod
    def _get_databases(
        cls,
        ml: MLClient,
    ) -> Response:
        resp = ml.manage.databases.get_list(data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_database(
        cls,
        ml: MLClient,
        database: str,
        view: str,
    ) -> Response:
        resp = ml.manage.databases.get(
            database,
            data_format="json",
            view=view,
        )
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_database_properties(
        cls,
        ml: MLClient,
        database: str,
    ) -> Response:
        resp = ml.manage.databases.get_properties(
            database,
            data_format="json",
        )
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _put_database_properties(
        cls,
        ml: MLClient,
        database: str,
        body: dict,
    ) -> Response:
        resp = ml.manage.databases.put_properties(
            database,
            body,
        )
        assert resp.status_code == httpx.codes.NO_CONTENT

        return resp

    @classmethod
    def _create_database(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.databases.create(cls.TEST_DATABASE_CONFIG)
        assert resp.status_code == httpx.codes.CREATED

    @classmethod
    def _delete_database(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.databases.delete(cls.TEST_DATABASE_CONFIG["database-name"])
        assert resp.status_code == httpx.codes.NO_CONTENT

    @classmethod
    def _perform_action_on_database(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.databases.post(
            cls.TEST_DATABASE_CONFIG["database-name"],
            {"operation": "clear-database"},
        )
        assert resp.status_code == httpx.codes.OK


class TestServersManagement:
    TEST_SERVER_CONFIG: ClassVar[dict] = {
        "server-name": "TestServer",
        "root": "/",
        "port": 8100,
        "content-database": "Documents",
    }

    def test_servers_management(
        self,
        ml_client: MLClient,
    ):
        init_count = -1
        try:
            init_count = self._init_check(ml_client)
            self._create_server(ml_client)
            self._middle_check(ml_client, init_count)

            self._check_server_config(ml_client)
            self._update_server_properties(ml_client)
            self._check_server_properties(ml_client)
        finally:
            self._delete_server(ml_client)
            self._final_check(ml_client, init_count)

    @classmethod
    def _init_check(
        cls,
        ml: MLClient,
    ) -> int:
        resp = cls._get_servers(ml)

        data = resp.json()["server-default-list"]["list-items"]
        servers = data["list-item"]
        servers_names = [database["nameref"] for database in servers]
        assert cls.TEST_SERVER_CONFIG["server-name"] not in servers_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_servers(ml)

        data = resp.json()["server-default-list"]["list-items"]
        servers = data["list-item"]
        servers_names = [database["nameref"] for database in servers]
        assert cls.TEST_SERVER_CONFIG["server-name"] in servers_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_servers(ml)

        data = resp.json()["server-default-list"]["list-items"]
        servers = data["list-item"]
        servers_names = [database["nameref"] for database in servers]
        assert cls.TEST_SERVER_CONFIG["server-name"] not in servers_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_server_config(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_server(
            ml,
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
        ml: MLClient,
    ):
        cls._put_server_properties(
            ml,
            cls.TEST_SERVER_CONFIG["server-name"],
            {"enabled": False},
        )

    @classmethod
    def _check_server_properties(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_server_properties(
            ml,
            cls.TEST_SERVER_CONFIG["server-name"],
        )
        server_props = resp.json()
        assert server_props["root"] == cls.TEST_SERVER_CONFIG["root"]
        assert server_props["port"] == cls.TEST_SERVER_CONFIG["port"]
        assert server_props["enabled"] is False

    @classmethod
    def _get_servers(
        cls,
        ml: MLClient,
    ) -> Response:
        resp = ml.manage.servers.get_list(data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_server(
        cls,
        ml: MLClient,
        server: str,
        view: str,
    ) -> Response:
        resp = ml.manage.servers.get(
            server,
            "Default",
            data_format="json",
            view=view,
        )
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_server_properties(
        cls,
        ml: MLClient,
        server: str,
    ) -> Response:
        resp = ml.manage.servers.get_properties(
            server,
            "Default",
            data_format="json",
        )
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _put_server_properties(
        cls,
        ml: MLClient,
        server: str,
        body: dict,
    ) -> Response:
        resp = ml.manage.servers.put_properties(
            server,
            "Default",
            body,
        )
        assert resp.status_code == httpx.codes.NO_CONTENT

        return resp

    @classmethod
    def _create_server(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.servers.create(
            cls.TEST_SERVER_CONFIG,
            group_id="Default",
            server_type="http",
        )
        assert resp.status_code == httpx.codes.CREATED

    @classmethod
    def _delete_server(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.servers.delete(
            cls.TEST_SERVER_CONFIG["server-name"],
            "Default",
        )
        assert resp.status_code == httpx.codes.ACCEPTED
        ml.wait_for_restart(resp)


class TestForestsManagement:
    TEST_FOREST_CONFIG: ClassVar[dict] = {"forest-name": "test-forest-1"}

    @pytest.mark.ml_access
    def test_forest_management(
        self,
        ml_client: MLClient,
    ):
        init_count = -1
        try:
            init_count = self._init_check(ml_client)

            self._create_forest(ml_client)
            self._middle_check(ml_client, init_count)

            self._check_forest_config(ml_client)
            self._update_forest_properties(ml_client)
            self._check_forest_properties(ml_client)

            self._initiate_state_change_on_forest(ml_client)
            self._perform_action_on_forests(ml_client)
        finally:
            self._delete_forest(ml_client)
            self._final_check(ml_client, init_count)

    @classmethod
    def _init_check(
        cls,
        ml: MLClient,
    ) -> int:
        resp = cls._get_forests(ml)

        data = resp.json()["forest-default-list"]["list-items"]
        forests = data["list-item"]
        forests_names = [forest["nameref"] for forest in forests]
        assert cls.TEST_FOREST_CONFIG["forest-name"] not in forests_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_forests(ml)

        data = resp.json()["forest-default-list"]["list-items"]
        forests = data["list-item"]
        forests_names = [forest["nameref"] for forest in forests]
        assert cls.TEST_FOREST_CONFIG["forest-name"] in forests_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_forests(ml)

        data = resp.json()["forest-default-list"]["list-items"]
        forests = data["list-item"]
        forests_names = [forest["nameref"] for forest in forests]
        assert cls.TEST_FOREST_CONFIG["forest-name"] not in forests_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_forest_config(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_forest(
            ml,
            cls.TEST_FOREST_CONFIG["forest-name"],
            view="config",
        )
        forest_config = resp.json()["forest-config"]["config-properties"]
        assert forest_config["enabled"] is True
        assert forest_config["rebalancer-enable"] is True

    @classmethod
    def _update_forest_properties(
        cls,
        ml: MLClient,
    ):
        cls._put_forest_properties(
            ml,
            cls.TEST_FOREST_CONFIG["forest-name"],
            {"rebalancer-enable": False},
        )

    @classmethod
    def _check_forest_properties(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_forest_properties(
            ml,
            cls.TEST_FOREST_CONFIG["forest-name"],
        )
        forest_props = resp.json()
        assert forest_props["enabled"] is True
        assert forest_props["rebalancer-enable"] is False

    @classmethod
    def _get_forests(
        cls,
        ml: MLClient,
    ) -> Response:
        resp = ml.manage.forests.get_list(data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_forest(
        cls,
        ml: MLClient,
        forest: str,
        view: str,
    ) -> Response:
        resp = ml.manage.forests.get(forest, data_format="json", view=view)
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_forest_properties(
        cls,
        ml: MLClient,
        forest: str,
    ) -> Response:
        resp = ml.manage.forests.get_properties(forest, data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _put_forest_properties(
        cls,
        ml: MLClient,
        forest: str,
        body: dict,
    ) -> Response:
        resp = ml.manage.forests.put_properties(
            forest,
            body,
        )
        assert resp.status_code == httpx.codes.NO_CONTENT

        return resp

    @classmethod
    def _create_forest(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.forests.create(cls.TEST_FOREST_CONFIG)
        assert resp.status_code == httpx.codes.CREATED

    @classmethod
    def _delete_forest(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.forests.delete(
            cls.TEST_FOREST_CONFIG["forest-name"],
            level="full",
        )
        assert resp.status_code == httpx.codes.NO_CONTENT

    @classmethod
    def _initiate_state_change_on_forest(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.forests.post(
            cls.TEST_FOREST_CONFIG["forest-name"],
            {"state": "clear"},
        )
        assert resp.status_code == httpx.codes.OK

    @classmethod
    def _perform_action_on_forests(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.forests.put(
            body={
                "operation": "forest-migrate",
            },
        )
        assert resp.status_code == httpx.codes.BAD_REQUEST
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
        ml_client: MLClient,
    ):
        init_count = -1
        try:
            init_count = self._init_check(ml_client)
            self._create_role(ml_client)
            self._middle_check(ml_client, init_count)

            self._check_role_config(ml_client)
            self._update_role_properties(ml_client)
            self._check_role_properties(ml_client)
        finally:
            self._delete_role(ml_client)
            self._final_check(ml_client, init_count)

    @classmethod
    def _init_check(
        cls,
        ml: MLClient,
    ) -> int:
        resp = cls._get_roles(ml)

        data = resp.json()["role-default-list"]["list-items"]
        roles = data["list-item"]
        roles_names = [role["nameref"] for role in roles]
        assert cls.TEST_ROLE_CONFIG["role-name"] not in roles_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_roles(ml)

        data = resp.json()["role-default-list"]["list-items"]
        roles = data["list-item"]
        roles_names = [role["nameref"] for role in roles]
        assert cls.TEST_ROLE_CONFIG["role-name"] in roles_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_roles(ml)

        data = resp.json()["role-default-list"]["list-items"]
        roles = data["list-item"]
        roles_names = [role["nameref"] for role in roles]
        assert cls.TEST_ROLE_CONFIG["role-name"] not in roles_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_role_config(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_role(
            ml,
            cls.TEST_ROLE_CONFIG["role-name"],
        )
        role_config = resp.json()["role-default"]
        assert role_config["name"] == cls.TEST_ROLE_CONFIG["role-name"]
        assert role_config["description"] == cls.TEST_ROLE_CONFIG["description"]

    @classmethod
    def _update_role_properties(
        cls,
        ml: MLClient,
    ):
        cls._put_role_properties(
            ml,
            cls.TEST_ROLE_CONFIG["role-name"],
            {"description": cls.TEST_ROLE_CONFIG["description"].upper()},
        )

    @classmethod
    def _check_role_properties(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_role_properties(
            ml,
            cls.TEST_ROLE_CONFIG["role-name"],
        )
        role_config = resp.json()
        assert role_config["role-name"] == cls.TEST_ROLE_CONFIG["role-name"]
        assert role_config["description"] == cls.TEST_ROLE_CONFIG["description"].upper()

    @classmethod
    def _get_roles(
        cls,
        ml: MLClient,
    ) -> Response:
        resp = ml.manage.roles.get_list(data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_role(
        cls,
        ml: MLClient,
        role: str,
    ) -> Response:
        resp = ml.manage.roles.get(
            role,
            data_format="json",
        )
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_role_properties(
        cls,
        ml: MLClient,
        role: str,
    ) -> Response:
        resp = ml.manage.roles.get_properties(
            role,
            data_format="json",
        )
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _put_role_properties(
        cls,
        ml: MLClient,
        role: str,
        body: dict,
    ) -> Response:
        resp = ml.manage.roles.put_properties(
            role,
            body,
        )
        assert resp.status_code == httpx.codes.NO_CONTENT

        return resp

    @classmethod
    def _create_role(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.roles.create(cls.TEST_ROLE_CONFIG)
        assert resp.status_code == httpx.codes.CREATED

    @classmethod
    def _delete_role(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.roles.delete(cls.TEST_ROLE_CONFIG["role-name"])
        assert resp.status_code == httpx.codes.NO_CONTENT


class TestUsersManagement:
    TEST_USER_CONFIG: ClassVar[dict] = {
        "user-name": "test-user",
        "description": "A test user",
    }

    def test_users_management(
        self,
        ml_client: MLClient,
    ):
        init_count = -1
        try:
            init_count = self._init_check(ml_client)
            self._create_user(ml_client)
            self._middle_check(ml_client, init_count)

            self._check_user_config(ml_client)
            self._update_user_properties(ml_client)
            self._check_user_properties(ml_client)
        finally:
            self._delete_user(ml_client)
            self._final_check(ml_client, init_count)

    @classmethod
    def _init_check(
        cls,
        ml: MLClient,
    ) -> int:
        resp = cls._get_users(ml)

        data = resp.json()["user-default-list"]["list-items"]
        users = data["list-item"]
        users_names = [user["nameref"] for user in users]
        assert cls.TEST_USER_CONFIG["user-name"] not in users_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_users(ml)

        data = resp.json()["user-default-list"]["list-items"]
        users = data["list-item"]
        users_names = [user["nameref"] for user in users]
        assert cls.TEST_USER_CONFIG["user-name"] in users_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_users(ml)

        data = resp.json()["user-default-list"]["list-items"]
        users = data["list-item"]
        users_names = [user["nameref"] for user in users]
        assert cls.TEST_USER_CONFIG["user-name"] not in users_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_user_config(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_user(
            ml,
            cls.TEST_USER_CONFIG["user-name"],
        )
        user_config = resp.json()["user-default"]
        assert user_config["name"] == cls.TEST_USER_CONFIG["user-name"]
        assert user_config["description"] == cls.TEST_USER_CONFIG["description"]

    @classmethod
    def _update_user_properties(
        cls,
        ml: MLClient,
    ):
        cls._put_user_properties(
            ml,
            cls.TEST_USER_CONFIG["user-name"],
            {"description": cls.TEST_USER_CONFIG["description"].upper()},
        )

    @classmethod
    def _check_user_properties(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_user_properties(
            ml,
            cls.TEST_USER_CONFIG["user-name"],
        )
        user_config = resp.json()
        assert user_config["user-name"] == cls.TEST_USER_CONFIG["user-name"]
        assert user_config["description"] == cls.TEST_USER_CONFIG["description"].upper()

    @classmethod
    def _get_users(
        cls,
        ml: MLClient,
    ) -> Response:
        resp = ml.manage.users.get_list(data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_user(
        cls,
        ml: MLClient,
        user: str,
    ) -> Response:
        resp = ml.manage.users.get(
            user,
            data_format="json",
        )
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_user_properties(
        cls,
        ml: MLClient,
        user: str,
    ) -> Response:
        resp = ml.manage.users.get_properties(
            user,
            data_format="json",
        )
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _put_user_properties(
        cls,
        ml: MLClient,
        user: str,
        body: dict,
    ) -> Response:
        resp = ml.manage.users.put_properties(
            user,
            body,
        )
        assert resp.status_code == httpx.codes.NO_CONTENT

        return resp

    @classmethod
    def _create_user(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.users.create(cls.TEST_USER_CONFIG)
        assert resp.status_code == httpx.codes.CREATED

    @classmethod
    def _delete_user(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.users.delete(cls.TEST_USER_CONFIG["user-name"])
        assert resp.status_code == httpx.codes.NO_CONTENT


class TestDocumentsManagement:
    DOCUMENT_BODY_PART_1 = BodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": {
                "type": "attachment",
                "filename": "/some/dir/doc1.json",
            },
            "content": b'{"root": {"child": "data"}}',
        },
    )
    DOCUMENT_BODY_PART_2 = BodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": {
                "type": "attachment",
                "filename": "/some/dir/doc1.json",
            },
            "content": b'{"root2": {"child2": "data2"}}',
        },
    )

    def test_docs_management(
        self,
        ml_client: MLClient,
    ):
        try:
            self._check_does_not_exist(ml_client)

            self._create_document(ml_client)
            self._check_created(ml_client)

            self._update_document(ml_client)
            self._check_updated(ml_client)
        finally:
            self._delete_document(ml_client)
            self._check_does_not_exist(ml_client)

    @classmethod
    def _check_does_not_exist(
        cls,
        ml: MLClient,
    ):
        resp = ml.rest.documents.get(
            uri=cls.DOCUMENT_BODY_PART_1.disposition.filename,
            data_format="json",
        )
        assert resp.status_code == httpx.codes.NOT_FOUND
        assert resp.json()["errorResponse"]["messageCode"] == "RESTAPI-NODOCUMENT"

    @classmethod
    def _check_created(
        cls,
        ml: MLClient,
    ):
        resp = ml.rest.documents.get(
            uri=cls.DOCUMENT_BODY_PART_1.disposition.filename,
            data_format="json",
        )
        assert resp.status_code == httpx.codes.OK

        parsed_resp = MLResponseParser.parse(resp)
        assert parsed_resp == {"root": {"child": "data"}}

    @classmethod
    def _check_updated(
        cls,
        ml: MLClient,
    ):
        resp = ml.rest.documents.get(
            uri=cls.DOCUMENT_BODY_PART_1.disposition.filename,
            data_format="json",
        )
        assert resp.status_code == httpx.codes.OK

        parsed_resp = MLResponseParser.parse(resp)
        assert parsed_resp == {"root2": {"child2": "data2"}}

    @classmethod
    def _create_document(
        cls,
        ml: MLClient,
    ):
        resp = ml.rest.documents.post([cls.DOCUMENT_BODY_PART_1])
        assert resp.status_code == httpx.codes.OK

    @classmethod
    def _update_document(
        cls,
        ml: MLClient,
    ):
        resp = ml.rest.documents.post([cls.DOCUMENT_BODY_PART_2])
        assert resp.status_code == httpx.codes.OK

    @classmethod
    def _delete_document(
        cls,
        ml: MLClient,
    ):
        resp = ml.rest.documents.delete(
            cls.DOCUMENT_BODY_PART_1.disposition.filename,
        )
        assert resp.status_code == httpx.codes.NO_CONTENT
