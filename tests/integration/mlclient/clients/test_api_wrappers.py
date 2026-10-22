from __future__ import annotations

import datetime
from time import sleep
from typing import ClassVar
from xml.etree import ElementTree
from uuid import uuid4

import httpx
import pytest
from httpx import Response

from mlclient import MLClient
from mlclient.connection import MARKLOGIC_MANAGE_PORT
from mlclient.http import HTTPConfig
from mlclient.models import DocumentsBodyPart, TextDocument
from mlclient.responses import MLResponseParser

EVAL_XQUERY = (
    "xquery version '1.0-ml';\n\n"
    "declare variable $element external;\n\n"
    "<new-parent>{xdmp:unquote($element)/parent/child}</new-parent>"
)
INVOKE_ROOT = f"/mlclient-invoke-endpoint-test/{uuid4().hex}"
INVOKE_WORDS_MODULE = f"{INVOKE_ROOT}/words.xqy"
INVOKE_EMPTY_MODULE = f"{INVOKE_ROOT}/empty.xqy"
INVOKE_MODULES = {
    INVOKE_WORDS_MODULE: (
        'xquery version "1.0-ml";\n'
        "declare variable $word1 as xs:string external;\n"
        "declare variable $word2 as xs:string external;\n"
        '($word1, $word2, fn:concat($word1, " ", $word2))'
    ),
    INVOKE_EMPTY_MODULE: 'xquery version "1.0-ml"; ()',
}


@pytest.fixture(scope="class")
def ml_client():
    with MLClient() as ml:
        yield ml


class TestEvalEndpoint:
    @pytest.mark.ml_access
    def test_eval_returns_multipart_response(self, ml_client: MLClient):
        resp = ml_client.rest.eval.post(
            xquery=EVAL_XQUERY,
            variables={"element": "<parent><child/></parent>"},
        )

        assert resp.status_code == httpx.codes.OK
        parsed_resp = MLResponseParser.parse(resp, str)
        assert parsed_resp == "<new-parent><child/></new-parent>"


@pytest.fixture(scope="class")
def invoke_modules(ml_client: MLClient):
    database = ml_client.eval.xquery("xdmp:database-name(xdmp:modules-database())")
    ml_client.documents.write(
        [TextDocument(code, uri) for uri, code in INVOKE_MODULES.items()],
        database=database,
    )
    try:
        yield
    finally:
        ml_client.documents.delete(list(INVOKE_MODULES), database=database)


@pytest.mark.usefixtures("invoke_modules")
class TestInvokeEndpoint:
    @pytest.mark.ml_access
    def test_invoke_returns_one_part_per_item(self, ml_client: MLClient):
        resp = ml_client.rest.invoke.post(
            INVOKE_WORDS_MODULE,
            variables={"word1": "hello", "word2": "world"},
        )

        assert resp.status_code == httpx.codes.OK
        assert resp.headers["Content-Type"].startswith("multipart/mixed")
        parsed_resp = MLResponseParser.parse(resp, str)
        assert parsed_resp == ["hello", "world", "hello world"]

    @pytest.mark.ml_access
    def test_invoke_of_empty_result_has_no_body(self, ml_client: MLClient):
        resp = ml_client.rest.invoke.post(INVOKE_EMPTY_MODULE)

        assert resp.status_code == httpx.codes.OK
        assert resp.content == b""
        assert "Content-Type" not in resp.headers

    @pytest.mark.ml_access
    def test_invoke_of_missing_module_is_rejected(self, ml_client: MLClient):
        missing_module = f"{INVOKE_ROOT}/missing.xqy"

        resp = ml_client.rest.invoke.post(missing_module)

        assert resp.status_code == httpx.codes.BAD_REQUEST
        assert resp.headers["Content-Type"] == "text/html; charset=utf-8"
        assert (
            f"XDMP-MODNOTFOUND: (err:XQST0059) Module {missing_module} not found"
            in resp.text
        )


class TestHealthCheckEndpoint:
    @pytest.mark.ml_access
    def test_healthcheck_reports_running_server(self, ml_client: MLClient):
        assert ml_client.healthcheck() is True

    @pytest.mark.ml_access
    def test_healthcheck_raises_when_probing_an_authenticated_server(self):
        authenticated = HTTPConfig.resolve(port=MARKLOGIC_MANAGE_PORT, auth=None)
        with (
            MLClient(health_config=authenticated) as ml,
            pytest.raises(
                httpx.HTTPStatusError,
            ) as exc,
        ):
            ml.healthcheck()

        assert exc.value.response.status_code == httpx.codes.UNAUTHORIZED

    @pytest.mark.ml_access
    def test_cluster_healthcheck_reports_every_host_healthy(
        self,
        ml_client: MLClient,
    ):
        health = ml_client.cluster_healthcheck()

        assert health.healthy is True
        assert health.hosts
        assert all(health.hosts.values())


class TestAdministration:
    """Admin API flows that leave an initialized cluster unchanged.

    Every state-changing request is one MarkLogic refuses or one that has no
    effect on an initialized host, so the flows run against the shared test
    server. A cluster archive is never sent: an initialized host accepts it
    and replaces its own cluster configuration.
    """

    INVALID_LICENSE: ClassVar[dict] = {
        "license-key": "1234-5678-90AB",
        "licensee": "Example Licensee",
    }
    ADMIN_USER: ClassVar[dict] = {
        "admin-username": "admin",
        "admin-password": "admin",
    }
    UNKNOWN_GROUP: ClassVar[str] = "no-such-group"
    UNKNOWN_HOST: ClassVar[str] = "no-such-host.example.com"
    MANAGE_NS: ClassVar[str] = "http://marklogic.com/manage"

    @pytest.mark.ml_access
    def test_server_availability(self, ml_client: MLClient):
        timestamp = self._get_timestamp(ml_client)

        self._head_timestamp(ml_client)

        assert self._get_timestamp(ml_client) == timestamp

    @pytest.mark.ml_access
    def test_server_config_describes_the_host(self, ml_client: MLClient):
        server_config = ElementTree.fromstring(self._get_server_config(ml_client))

        host_name = ml_client.eval.xquery("xdmp:host-name()")
        assert server_config.findtext(f"{{{self.MANAGE_NS}}}host-name") == host_name
        assert server_config.findtext(f"{{{self.MANAGE_NS}}}bind-port") == "7999"

    @pytest.mark.ml_access
    def test_initialized_server_is_not_initialized_again(self, ml_client: MLClient):
        timestamp = self._get_timestamp(ml_client)

        self._init_without_restart(ml_client)
        self._check_invalid_license_is_rejected(ml_client)
        self._check_instance_admin_is_rejected(ml_client)

        assert self._get_timestamp(ml_client) == timestamp

    @pytest.mark.ml_access
    def test_cluster_join_is_validated(self, ml_client: MLClient):
        server_config = self._get_server_config(ml_client)

        self._check_self_join_is_rejected(ml_client, server_config)
        self._check_join_to_unknown_group_is_rejected(ml_client, server_config)

    @pytest.mark.ml_access
    def test_host_removal_is_validated(self, ml_client: MLClient):
        self._check_removal_of_host_with_forests_is_rejected(ml_client)
        self._check_removal_of_unknown_host_is_rejected(ml_client)

    @classmethod
    def _get_timestamp(
        cls,
        ml: MLClient,
    ) -> str:
        resp = ml.admin.get_timestamp()
        assert resp.status_code == httpx.codes.OK
        assert resp.headers["content-type"] == "text/plain; charset=UTF-8"

        return resp.text

    @classmethod
    def _head_timestamp(
        cls,
        ml: MLClient,
    ):
        resp = ml.admin.head_timestamp()
        assert resp.status_code == httpx.codes.OK
        assert resp.content == b""

    @classmethod
    def _get_server_config(
        cls,
        ml: MLClient,
    ) -> str:
        resp = ml.admin.get_server_config()
        assert resp.status_code == httpx.codes.OK
        assert resp.headers["content-type"] == "application/xml; charset=UTF-8"

        return resp.text

    @classmethod
    def _init_without_restart(
        cls,
        ml: MLClient,
    ):
        resp = ml.admin.post_init(data_format="json")
        assert resp.status_code == httpx.codes.NO_CONTENT

    @classmethod
    def _check_invalid_license_is_rejected(
        cls,
        ml: MLClient,
    ):
        resp = ml.admin.post_init(body=cls.INVALID_LICENSE, data_format="json")
        cls._assert_error(resp, httpx.codes.BAD_REQUEST, "MANAGE-INVALIDLICENSE")

    @classmethod
    def _check_instance_admin_is_rejected(
        cls,
        ml: MLClient,
    ):
        resp = ml.admin.post_instance_admin(cls.ADMIN_USER, data_format="json")
        assert resp.status_code == httpx.codes.BAD_REQUEST
        error = MLResponseParser.parse(resp)["errorResponse"]
        assert error["message"] == "Initialization cannot be repeated."

    @classmethod
    def _check_self_join_is_rejected(
        cls,
        ml: MLClient,
        server_config: str,
    ):
        resp = ml.admin.post_cluster_config(
            server_config=server_config,
            group="Default",
        )
        cls._assert_error(resp, httpx.codes.BAD_REQUEST, "MANAGE-SELFJOIN")

    @classmethod
    def _check_join_to_unknown_group_is_rejected(
        cls,
        ml: MLClient,
        server_config: str,
    ):
        resp = ml.admin.post_cluster_config(
            server_config=server_config,
            group=cls.UNKNOWN_GROUP,
        )
        cls._assert_error(resp, httpx.codes.BAD_REQUEST, "MANAGE-INVALIDPARAM")

    @classmethod
    def _check_removal_of_host_with_forests_is_rejected(
        cls,
        ml: MLClient,
    ):
        resp = ml.admin.delete_host_config()
        cls._assert_error(resp, httpx.codes.BAD_REQUEST, "MANAGE-PRECONDITIONFAILED")

    @classmethod
    def _check_removal_of_unknown_host_is_rejected(
        cls,
        ml: MLClient,
    ):
        resp = ml.admin.delete_host_config(remote_host=cls.UNKNOWN_HOST)
        cls._assert_error(resp, httpx.codes.NOT_FOUND, "XDMP-NOSUCHHOST")

    @classmethod
    def _assert_error(
        cls,
        resp: Response,
        status_code: int,
        message_code: str,
    ):
        assert resp.status_code == status_code
        error = MLResponseParser.parse(resp)["errorResponse"]
        assert error["messageCode"] == message_code


class TestTransactionsEndpoint:
    @pytest.mark.ml_access
    def test_transaction_lifecycle_returns_expected_status_codes(
        self,
        ml_client: MLClient,
    ):
        txid = None
        try:
            create_resp = ml_client.rest.transactions.create()
            assert create_resp.status_code == httpx.codes.SEE_OTHER
            txid = create_resp.headers["Location"].rsplit("/", 1)[-1]

            status_resp = ml_client.rest.transactions.get(txid, data_format="json")
            assert status_resp.status_code == httpx.codes.OK
            status = MLResponseParser.parse(status_resp)["transaction-status"]
            assert status["transaction-id"] == txid

            commit_resp = ml_client.rest.transactions.post(txid, result="commit")
            assert commit_resp.status_code == httpx.codes.NO_CONTENT
            txid = None
        finally:
            self._rollback_quietly(ml_client, txid)

    @pytest.mark.ml_access
    def test_status_of_committed_transaction_is_rejected(self, ml_client: MLClient):
        create_resp = ml_client.rest.transactions.create()
        txid = create_resp.headers["Location"].rsplit("/", 1)[-1]
        ml_client.rest.transactions.post(txid, result="commit")

        status_resp = ml_client.rest.transactions.get(txid, data_format="json")

        assert status_resp.status_code == httpx.codes.BAD_REQUEST
        error = MLResponseParser.parse(status_resp)["errorResponse"]
        assert error["messageCode"] == "REST-INVALIDPARAM"

    @classmethod
    def _rollback_quietly(cls, ml: MLClient, txid: str | None):
        if txid is not None:
            ml.rest.transactions.post(txid, result="rollback")


class TestHostsManagement:
    TEST_HOST_PROPERTIES: ClassVar[dict] = {"zone": "test-zone"}

    @pytest.mark.ml_access
    def test_hosts_management(
        self,
        ml_client: MLClient,
    ):
        host = self._check_host_is_listed(ml_client)
        initial_props = self._get_host_properties(ml_client, host).json()
        try:
            self._check_host_config(ml_client, host)
            self._update_host_properties(ml_client, host)
            self._check_host_properties(ml_client, host)

            self._initiate_invalid_state_change_on_host(ml_client, host)
        finally:
            self._put_host_properties(ml_client, host, {"zone": initial_props["zone"]})

    @pytest.mark.ml_access
    @pytest.mark.parametrize(
        "view",
        ["default", "status", "metrics", "schema", "properties-schema", "describe"],
    )
    def test_supported_host_views(self, ml_client: MLClient, view: str):
        response = ml_client.manage.hosts.get_list(view=view)
        assert response.status_code == httpx.codes.OK
        assert "xml" in response.headers["content-type"]

    @pytest.mark.ml_access
    def test_schema_view_rejects_json(self, ml_client: MLClient):
        response = ml_client.manage.hosts.get_list(view="schema", data_format="json")
        assert response.status_code == httpx.codes.BAD_REQUEST
        assert response.json()["errorResponse"]["messageCode"] == "MANAGE-INVALIDPARAM"

    @classmethod
    def _check_host_is_listed(
        cls,
        ml: MLClient,
    ) -> str:
        resp = cls._get_hosts(ml)

        data = resp.json()["host-default-list"]["list-items"]
        hosts_names = [host["nameref"] for host in data["list-item"]]
        host = ml.eval.xquery("xdmp:host-name()")
        assert host in hosts_names
        assert data["list-count"]["value"] == len(hosts_names)

        return host

    @classmethod
    def _check_host_config(
        cls,
        ml: MLClient,
        host: str,
    ):
        resp = cls._get_host(ml, host, view="config")
        host_config = resp.json()["host-config"]
        assert host_config["name"] == host
        assert host_config["config-properties"]["bind-port"] == 7999

    @classmethod
    def _update_host_properties(
        cls,
        ml: MLClient,
        host: str,
    ):
        cls._put_host_properties(ml, host, cls.TEST_HOST_PROPERTIES)

    @classmethod
    def _check_host_properties(
        cls,
        ml: MLClient,
        host: str,
    ):
        resp = cls._get_host_properties(ml, host)
        host_props = resp.json()
        assert host_props["host-name"] == host
        assert host_props["zone"] == cls.TEST_HOST_PROPERTIES["zone"]

    @classmethod
    def _get_hosts(
        cls,
        ml: MLClient,
    ) -> Response:
        resp = ml.manage.hosts.get_list(data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_host(
        cls,
        ml: MLClient,
        host: str,
        view: str,
    ) -> Response:
        resp = ml.manage.hosts.get(host, data_format="json", view=view)
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_host_properties(
        cls,
        ml: MLClient,
        host: str,
    ) -> Response:
        resp = ml.manage.hosts.get_properties(host, data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _put_host_properties(
        cls,
        ml: MLClient,
        host: str,
        body: dict,
    ) -> Response:
        resp = ml.manage.hosts.put_properties(
            host,
            body,
        )
        assert resp.status_code == httpx.codes.NO_CONTENT

        return resp

    @classmethod
    def _initiate_invalid_state_change_on_host(
        cls,
        ml: MLClient,
        host: str,
    ):
        resp = ml.manage.hosts.post(host, {"state": "restart", "failover": "yes"})
        assert resp.status_code == httpx.codes.BAD_REQUEST
        err = MLResponseParser.parse(resp)["errorResponse"]
        assert err["messageCode"] == "REST-INVALIDTYPE"
        assert err["message"] == (
            "REST-INVALIDTYPE: (rest:INVALIDTYPE) "
            "Invalid type in failover: yes is not a value of type boolean"
        )


class TestLogsEndpoint:
    TEST_LOGS_COUNT = 10

    @pytest.mark.ml_access
    def test_error_logs_contain_produced_entries(self, ml_client: MLClient):
        self._produce_test_logs(ml_client)
        sleep(1)

        resp = ml_client.manage.logs.get(
            filename=f"{ml_client.http.config.port}_ErrorLog.txt",
            data_format="json",
            start_time=str(datetime.date.today()),
            regex="Test Log .{1,2}",
        )

        assert resp.status_code == httpx.codes.OK
        logfile = resp.json()["logfile"]
        assert "message" not in logfile
        assert isinstance(logfile.get("log"), list) or len(logfile) == 6
        assert len(logfile["log"]) % self.TEST_LOGS_COUNT == 0

    @pytest.mark.ml_access
    def test_access_logs_record_eval_requests(self, ml_client: MLClient):
        self._produce_test_logs(ml_client)
        sleep(1)

        resp = ml_client.manage.logs.get(
            filename=f"{ml_client.http.config.port}_AccessLog.txt",
            data_format="json",
        )

        assert resp.status_code == httpx.codes.OK
        logfile = resp.json()["logfile"]
        assert "log" not in logfile
        assert isinstance(logfile.get("message"), str) or len(logfile) == 6
        eval_logs = [
            line
            for line in logfile["message"].split("\n")
            if '"POST /v1/eval HTTP/1.1"' in line and "python-httpx" in line
        ]
        assert len(eval_logs) >= self.TEST_LOGS_COUNT

    @pytest.mark.ml_access
    def test_request_logs_have_expected_structure(self, ml_client: MLClient):
        resp = ml_client.manage.logs.get(
            filename=f"{ml_client.http.config.port}_RequestLog.txt",
            data_format="json",
        )

        assert resp.status_code == httpx.codes.OK
        logfile = resp.json()["logfile"]
        assert "log" not in logfile
        assert isinstance(logfile.get("message"), str) or len(logfile) == 6

    @classmethod
    def _produce_test_logs(cls, ml: MLClient):
        for i in range(1, cls.TEST_LOGS_COUNT + 1):
            ml.rest.eval.post(xquery=f'xdmp:log("Test Log {i}", "error")')


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


class TestGroupsManagement:
    TEST_GROUP_CONFIG: ClassVar[dict] = {"group-name": "test-group"}

    @pytest.mark.ml_access
    def test_groups_management(
        self,
        ml_client: MLClient,
    ):
        init_count = -1
        try:
            init_count = self._init_check(ml_client)

            self._create_group(ml_client)
            self._middle_check(ml_client, init_count)

            self._check_group_config(ml_client)
            self._update_group_properties(ml_client)
            self._check_group_properties(ml_client)

            self._restart_group_without_hosts(ml_client)
        finally:
            self._delete_group(ml_client)
            self._final_check(ml_client, init_count)

    @classmethod
    def _init_check(
        cls,
        ml: MLClient,
    ) -> int:
        resp = cls._get_groups(ml)

        data = resp.json()["group-default-list"]["list-items"]
        groups = data["list-item"]
        groups_names = [group["nameref"] for group in groups]
        assert cls.TEST_GROUP_CONFIG["group-name"] not in groups_names

        return data["list-count"]["value"]

    @classmethod
    def _middle_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_groups(ml)

        data = resp.json()["group-default-list"]["list-items"]
        groups = data["list-item"]
        groups_names = [group["nameref"] for group in groups]
        assert cls.TEST_GROUP_CONFIG["group-name"] in groups_names

        middle_count = data["list-count"]["value"]
        assert middle_count == init_count + 1

    @classmethod
    def _final_check(
        cls,
        ml: MLClient,
        init_count: int,
    ):
        resp = cls._get_groups(ml)

        data = resp.json()["group-default-list"]["list-items"]
        groups = data["list-item"]
        groups_names = [group["nameref"] for group in groups]
        assert cls.TEST_GROUP_CONFIG["group-name"] not in groups_names

        final_count = data["list-count"]["value"]
        assert init_count in (-1, final_count)

    @classmethod
    def _check_group_config(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_group(
            ml,
            cls.TEST_GROUP_CONFIG["group-name"],
            view="config",
        )
        group_config = resp.json()["group-config"]["config-properties"]
        assert group_config["file-log-level"] == "info"
        assert group_config["failover-enable"] is True

    @classmethod
    def _update_group_properties(
        cls,
        ml: MLClient,
    ):
        cls._put_group_properties(
            ml,
            cls.TEST_GROUP_CONFIG["group-name"],
            {"file-log-level": "debug"},
        )

    @classmethod
    def _check_group_properties(
        cls,
        ml: MLClient,
    ):
        resp = cls._get_group_properties(
            ml,
            cls.TEST_GROUP_CONFIG["group-name"],
        )
        group_props = resp.json()
        assert group_props["group-name"] == cls.TEST_GROUP_CONFIG["group-name"]
        assert group_props["file-log-level"] == "debug"

    @classmethod
    def _get_groups(
        cls,
        ml: MLClient,
    ) -> Response:
        resp = ml.manage.groups.get_list(data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_group(
        cls,
        ml: MLClient,
        group: str,
        view: str,
    ) -> Response:
        resp = ml.manage.groups.get(group, data_format="json", view=view)
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _get_group_properties(
        cls,
        ml: MLClient,
        group: str,
    ) -> Response:
        resp = ml.manage.groups.get_properties(group, data_format="json")
        assert resp.status_code == httpx.codes.OK

        return resp

    @classmethod
    def _put_group_properties(
        cls,
        ml: MLClient,
        group: str,
        body: dict,
    ) -> Response:
        resp = ml.manage.groups.put_properties(
            group,
            body,
        )
        assert resp.status_code == httpx.codes.NO_CONTENT

        return resp

    @classmethod
    def _create_group(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.groups.create(cls.TEST_GROUP_CONFIG)
        assert resp.status_code == httpx.codes.CREATED

    @classmethod
    def _delete_group(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.groups.delete(cls.TEST_GROUP_CONFIG["group-name"])
        assert resp.status_code == httpx.codes.NO_CONTENT

    @classmethod
    def _restart_group_without_hosts(
        cls,
        ml: MLClient,
    ):
        resp = ml.manage.groups.post(
            cls.TEST_GROUP_CONFIG["group-name"],
            {"operation": "restart-group"},
        )
        assert resp.status_code == httpx.codes.BAD_REQUEST
        err = resp.json()["errorResponse"]
        assert err["messageCode"] == "MANAGE-PRECONDITIONFAILED"
        assert err["message"] == (
            "MANAGE-PRECONDITIONFAILED: (err:FOER0000) Precondition not met: "
            "Cannot restart group, there are no hosts in group"
        )


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
    DOCUMENT_BODY_PART_1 = DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": {
                "type": "attachment",
                "filename": "/some/dir/doc1.json",
            },
            "content": b'{"root": {"child": "data"}}',
        },
    )
    DOCUMENT_BODY_PART_2 = DocumentsBodyPart(
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
