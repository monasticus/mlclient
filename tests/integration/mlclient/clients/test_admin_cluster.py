from __future__ import annotations

import time
from typing import ClassVar
from xml.etree import ElementTree

import httpx
import pytest
from testcontainers.core.container import DockerContainer

from mlclient import MLClient
from mlclient.http import HTTPConfig

MARKLOGIC_REST_PORT = 8000
MARKLOGIC_ADMIN_PORT = 8001
MARKLOGIC_MANAGE_PORT = 8002


class TestAdminClusterLifecycle:
    """The Admin API cluster lifecycle on two hosts the test owns.

    Initialization, cluster joins and host removal change a host for good, so
    they run against fresh hosts started for this class, never against the
    shared test server.
    """

    ADMIN_USER: ClassVar[dict] = {
        "admin-username": "admin",
        "admin-password": "admin",
        "realm": "public",
    }
    GROUP: ClassVar[str] = "Default"
    MANAGE_NS: ClassVar[str] = "http://marklogic.com/manage"
    RESTART_TIMEOUT: ClassVar[float] = 180

    @pytest.mark.ml_cluster_lifecycle
    def test_cluster_lifecycle(
        self,
        uninitialized_marklogic_nodes: list[DockerContainer],
    ):
        bootstrap_node, joining_node = uninitialized_marklogic_nodes
        with (
            self._client(bootstrap_node) as bootstrap,
            self._client(joining_node) as joining,
        ):
            self._initialize(bootstrap)
            self._check_initialization_is_not_repeated(bootstrap)
            self._install_admin(bootstrap)
            bootstrap_host = self._host_name(bootstrap)

            joining_host = self._join(bootstrap, joining)
            self._check_hosts(bootstrap, [bootstrap_host, joining_host])

            self._remove_itself(joining)
            self._check_hosts(bootstrap, [bootstrap_host])

            self._join(bootstrap, joining)
            self._check_hosts(bootstrap, [bootstrap_host, joining_host])

            self._remove_remote_host(bootstrap, joining_host)
            self._check_hosts(bootstrap, [bootstrap_host])

    @classmethod
    def _client(
        cls,
        node: DockerContainer,
    ) -> MLClient:
        host = node.get_container_host_ip()

        def config(port: int) -> HTTPConfig:
            return HTTPConfig.resolve(host=host, port=int(node.get_exposed_port(port)))

        return MLClient(
            config=config(MARKLOGIC_REST_PORT),
            manage_config=config(MARKLOGIC_MANAGE_PORT),
            admin_config=config(MARKLOGIC_ADMIN_PORT),
        )

    @classmethod
    def _initialize(
        cls,
        ml: MLClient,
    ):
        timestamp = cls._get_timestamp(ml)

        resp = ml.admin.post_init(data_format="json")
        assert resp.status_code == httpx.codes.ACCEPTED
        assert resp.headers["Location"] == "/admin/v1/timestamp"

        cls._wait_for_restart(ml, timestamp)

    @classmethod
    def _check_initialization_is_not_repeated(
        cls,
        ml: MLClient,
    ):
        resp = ml.admin.post_init(data_format="json")
        assert resp.status_code == httpx.codes.NO_CONTENT

    @classmethod
    def _install_admin(
        cls,
        ml: MLClient,
    ):
        timestamp = cls._get_timestamp(ml)

        resp = ml.admin.post_instance_admin(cls.ADMIN_USER, data_format="json")
        assert resp.status_code == httpx.codes.ACCEPTED
        assert resp.json()["restart"]["link"]["uriref"] == "/admin/v1/timestamp"

        cls._wait_for_restart(ml, timestamp)

    @classmethod
    def _join(
        cls,
        bootstrap: MLClient,
        joining: MLClient,
    ) -> str:
        cls._initialize(joining)
        server_config = joining.admin.get_server_config()
        assert server_config.status_code == httpx.codes.OK

        cluster_config = bootstrap.admin.post_cluster_config(
            server_config=server_config.text,
            group=cls.GROUP,
        )
        assert cluster_config.status_code == httpx.codes.OK
        assert cluster_config.headers["Content-Type"] == "application/zip"

        timestamp = cls._get_timestamp(joining)
        resp = joining.admin.post_cluster_config(cluster_config=cluster_config.content)
        assert resp.status_code == httpx.codes.ACCEPTED
        cls._wait_for_restart(joining, timestamp)

        return cls._config_host_name(server_config.text)

    @classmethod
    def _remove_itself(
        cls,
        ml: MLClient,
    ):
        timestamp = cls._get_timestamp(ml)

        resp = ml.admin.delete_host_config()
        assert resp.status_code == httpx.codes.ACCEPTED
        assert "<uriref>/admin/v1/timestamp</uriref>" in resp.text

        cls._wait_for_restart(ml, timestamp)

    @classmethod
    def _remove_remote_host(
        cls,
        ml: MLClient,
        host: str,
    ):
        resp = ml.admin.delete_host_config(remote_host=host)
        assert resp.status_code == httpx.codes.NO_CONTENT

    @classmethod
    def _check_hosts(
        cls,
        ml: MLClient,
        expected_hosts: list[str],
    ):
        resp = ml.manage.hosts.get_list(data_format="json")
        assert resp.status_code == httpx.codes.OK

        hosts = resp.json()["host-default-list"]["list-items"]["list-item"]
        assert sorted(host["nameref"] for host in hosts) == sorted(expected_hosts)

    @classmethod
    def _host_name(
        cls,
        ml: MLClient,
    ) -> str:
        resp = ml.admin.get_server_config()
        assert resp.status_code == httpx.codes.OK

        return cls._config_host_name(resp.text)

    @classmethod
    def _config_host_name(
        cls,
        server_config: str,
    ) -> str:
        return ElementTree.fromstring(server_config).findtext(
            f"{{{cls.MANAGE_NS}}}host-name",
        )

    @classmethod
    def _get_timestamp(
        cls,
        ml: MLClient,
    ) -> str:
        resp = ml.admin.get_timestamp()
        assert resp.status_code == httpx.codes.OK

        return resp.text

    @classmethod
    def _wait_for_restart(
        cls,
        ml: MLClient,
        previous_timestamp: str,
    ):
        # ml.wait_for_restart() probes the default Admin port, not the port
        # Docker publishes, so the restart is detected by a new timestamp.
        deadline = time.monotonic() + cls.RESTART_TIMEOUT
        while time.monotonic() < deadline:
            try:
                resp = ml.admin.get_timestamp()
            except httpx.TransportError:
                resp = None
            if resp is not None and resp.is_success and resp.text != previous_timestamp:
                return
            time.sleep(1)
        pytest.fail(f"MarkLogic did not restart within {cls.RESTART_TIMEOUT} seconds")
