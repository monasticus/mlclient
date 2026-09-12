from __future__ import annotations

import pytest
from httpx_retries import Retry

from mlclient import MLClient
from mlclient.services import LogLevelService


@pytest.fixture(scope="class")
def ml_client():
    with MLClient() as ml:
        yield ml


@pytest.fixture(scope="class")
def denied_client():
    with MLClient(
        username="log-level-invalid-user",
        password="invalid",
        retry=Retry(total=0),
    ) as ml:
        yield ml


class TestLogLevelService:
    TARGETS = (
        pytest.param({"log_type": "file"}, id="group-file"),
        pytest.param({"log_type": "system"}, id="group-system"),
        pytest.param({"server": "App-Services"}, id="app-server-file"),
    )

    @pytest.mark.ml_access
    @pytest.mark.parametrize("target", TARGETS)
    def test_eval_round_trip(
        self, ml_client: MLClient, denied_client: MLClient, target: dict,
    ):
        levels = LogLevelService(ml_client.rest, denied_client.manage)
        reader = LogLevelService(ml_client.rest, ml_client.manage)
        self._assert_round_trip(levels, reader, target)

    @pytest.mark.ml_access
    @pytest.mark.parametrize("target", TARGETS)
    def test_manage_fallback_round_trip(
        self, ml_client: MLClient, denied_client: MLClient, target: dict,
    ):
        denied = denied_client.rest.eval.post(xquery="1")
        assert denied.status_code == 401
        levels = LogLevelService(ml_client.rest, ml_client.manage)
        fallback = LogLevelService(denied_client.rest, ml_client.manage)
        self._assert_round_trip(fallback, levels, target)

    @classmethod
    def _assert_round_trip(
        cls, service: LogLevelService, reader: LogLevelService, target: dict,
    ):
        """Change a level, verify persistence, and restore it even on failure."""
        original = reader.get(**target)
        replacement = "notice" if original == "info" else "info"
        try:
            assert service.get(**target) == original
            assert service.set(replacement, timeout=5, **target) == replacement
            assert service.get(timeout=5, **target) == replacement
            assert reader.get(**target) == replacement
        finally:
            reader.set(original, **target)
        assert reader.get(**target) == original
