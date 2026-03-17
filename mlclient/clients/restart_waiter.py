"""Restart readiness support for MarkLogic clients."""

from __future__ import annotations

import asyncio
import json
import ssl
import time
from typing import NoReturn, Union
from xml.etree import ElementTree

import httpx
from httpx import AsyncClient, Auth, Response, AsyncHTTPTransport
from httpx_retries import Retry, RetryTransport
from mlclient import constants as const

# See ml_client._SHARED_SSL_CONTEXT for rationale (avoid repeated CA bundle loading).
_SHARED_SSL_CONTEXT = ssl.create_default_context()

_RestartTimestampBaseline = Union[asyncio.Future, str, None]
_MARKLOGIC_ADMIN_API_PORT = 8001
_MARKLOGIC_MANAGE_API_PORT = 8002
_HOSTS_ENDPOINT = "/manage/v2/hosts"
_RESTART_TIMESTAMP_PATH = "/admin/v1/timestamp"


class RestartWaiter:
    """Wait for MarkLogic readiness after a restart-signaling response."""

    def __init__(
        self,
        protocol: str,
        host: str,
        auth: Auth,
        default_retry: Retry,
    ):
        self._protocol = protocol
        self._host = host
        self._auth = auth
        self._default_retry = default_retry

    def wait_for_restart_completion(
        self,
        response: Response | None,
        timeout: float,
        poll_interval: float,
        retry: Retry | None = None,
    ) -> None:
        """Wait until the Admin timestamp endpoint confirms MarkLogic readiness.

        Some MarkLogic Management and Admin API operations apply configuration
        changes asynchronously. When such an operation triggers a restart,
        MarkLogic returns ``202 Accepted`` together with
        ``Location: /admin/v1/timestamp`` and a ``restart`` payload body
        containing one or more ``last-startup`` timestamps keyed by host id.
        The Admin API documentation defines ``GET /admin/v1/timestamp`` on port
        ``8001`` as the readiness probe used to verify when MarkLogic is
        operational again. This endpoint is host-specific; operations which
        restart multiple hosts therefore require checking each affected host
        separately. There is no single cluster-wide readiness endpoint involved.

        This helper supports two usage modes:

        - If ``response`` is omitted or is not recognized as a restart
          response, the method performs a single readiness probe against
          ``/admin/v1/timestamp`` using a retry policy tailored to restart
          windows.
        - If ``response`` is recognized as a restart response, the method waits
          until all affected hosts reported in the restart payload return
          ``200 OK`` from ``/admin/v1/timestamp`` with timestamps different from
          their corresponding ``last-startup`` values. These host checks run
          concurrently. The current client host is probed immediately while
          host-id to host-name resolution from ``/manage/v2/hosts`` runs in
          parallel for the remaining hosts. If the current client host is one of
          the affected hosts, the method still waits for a timestamp newer than
          that host's own ``last-startup`` value.

        During an actual restart the timestamp endpoint can temporarily return
        ``503 Service Unavailable`` or fail with transport-level errors such as
        timeouts, connection resets, or protocol disconnects.

        Parameters
        ----------
        response : Response | None
            Optional response returned by an operation that may have initiated a
            restart.
        timeout : float
            Maximum number of seconds to wait for a new startup timestamp when
            the provided response is a recognized restart response.
        poll_interval : float
            Delay between polls after receiving a stale timestamp.
        retry : Retry | None
            Retry strategy used for the Admin readiness checks. If omitted, the
            waiter's default retry strategy is used.

        Raises
        ------
        ValueError
            If the restart response includes multiple hosts and their host ids
            cannot be resolved to MarkLogic host names through the Manage API.
        TimeoutError
            If a recognized restart response is provided but MarkLogic does not
            report a new startup timestamp before ``timeout`` expires.
        AssertionError
            If the readiness probe does not return ``200 OK``.
        """
        restart_timestamps = self._get_last_startup_by_host(response)
        self._run_async(
            self._wait_for_restart_readiness(
                restart_timestamps,
                timeout,
                poll_interval,
                retry or self._default_retry,
            ),
        )

    @staticmethod
    def is_restart_response(
        response: Response | None,
    ) -> bool:
        """Return whether a response signals MarkLogic restart readiness flow."""
        if response is None or response.status_code != httpx.codes.ACCEPTED:
            return False

        location = response.headers.get("Location")
        if not location or not location.endswith(_RESTART_TIMESTAMP_PATH):
            return False

        return bool(response.content)

    @staticmethod
    def _get_last_startup_by_host(
        response: Response | None,
    ) -> dict[str, str]:
        """Return restart payload timestamps keyed by host id."""
        if not RestartWaiter.is_restart_response(response):
            return {}

        content_type = response.headers.get(const.HEADER_NAME_CONTENT_TYPE, "")
        if "json" in content_type:
            return RestartWaiter._get_last_startup_by_host_from_json(
                response.content,
            )
        return RestartWaiter._get_last_startup_by_host_from_xml(
            response.content,
        )

    @staticmethod
    def _get_last_startup_by_host_from_json(
        content: bytes,
    ) -> dict[str, str]:
        """Parse restart timestamps from a MarkLogic JSON payload."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return {}

        restart = data.get("restart")
        if not isinstance(restart, dict):
            return {}

        link = restart.get("link")
        if (
            not isinstance(link, dict)
            or link.get("uriref") != _RESTART_TIMESTAMP_PATH
        ):
            return {}

        last_startup = restart.get("last-startup")
        items = last_startup if isinstance(last_startup, list) else [last_startup]
        return {
            item["host-id"]: item["value"]
            for item in items
            if (
                isinstance(item, dict)
                and item.get("host-id")
                and item.get("value")
            )
        }

    @staticmethod
    def _get_last_startup_by_host_from_xml(
        content: bytes,
    ) -> dict[str, str]:
        """Parse restart timestamps from a MarkLogic XML payload."""
        try:
            root = ElementTree.fromstring(content)
        except ElementTree.ParseError:
            return {}

        if not root.tag.endswith("restart"):
            return {}

        link = root.find(".//{*}uriref")
        if link is None or (link.text or "").strip() != _RESTART_TIMESTAMP_PATH:
            return {}

        timestamps_by_host: dict[str, str] = {}
        for elem in root.findall(".//{*}last-startup"):
            host_id = elem.attrib.get("host-id")
            timestamp = (elem.text or "").strip()
            if host_id and timestamp:
                timestamps_by_host[host_id] = timestamp
        return timestamps_by_host

    @staticmethod
    def _run_async(coroutine) -> None:
        """Run an async readiness workflow from a synchronous API."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(coroutine)
            return

        msg = (
            "wait_for_restart_completion() cannot be used from a running event "
            "loop. Use a synchronous context or add an async variant."
        )
        coroutine.close()
        raise RuntimeError(msg)

    async def _wait_for_restart_readiness(
        self,
        restart_timestamps: dict[str, str],
        timeout: float,
        poll_interval: float,
        retry: Retry,
    ) -> None:
        """Wait for restart readiness, probing the current host immediately."""
        if not restart_timestamps:
            await self._wait_for_host_ready(
                self._host,
                None,
                timeout,
                poll_interval,
                retry,
            )
            return

        if len(restart_timestamps) == 1:
            await self._wait_for_host_ready(
                self._host,
                next(iter(restart_timestamps.values())),
                timeout,
                poll_interval,
                retry,
            )
            return

        await self._wait_for_all_restart_hosts_ready(
            restart_timestamps,
            timeout,
            poll_interval,
            retry,
        )

    async def _wait_for_all_restart_hosts_ready(
        self,
        restart_timestamps: dict[str, str],
        timeout: float,
        poll_interval: float,
        retry: Retry,
    ) -> None:
        """Wait for all hosts from a multi-host restart response."""
        current_host_baseline, current_host_task, host_names_task = (
            self._start_current_host_readiness_wait(
                timeout,
                poll_interval,
                retry,
            )
        )
        restart_hosts_by_name = await self._resolve_restart_hosts(
            restart_timestamps,
            host_names_task,
            current_host_task,
            current_host_baseline,
        )
        await asyncio.gather(
            current_host_task,
            *[
                asyncio.create_task(
                    self._wait_for_host_ready(
                        host,
                        baseline_timestamp,
                        timeout,
                        poll_interval,
                        retry,
                    ),
                )
                for host, baseline_timestamp in restart_hosts_by_name.items()
                if host != self._host
            ],
        )

    def _start_current_host_readiness_wait(
        self,
        timeout: float,
        poll_interval: float,
        retry: Retry,
    ) -> tuple[
        asyncio.Future[str | None],
        asyncio.Task[None],
        asyncio.Task[dict[str, str]],
    ]:
        """Start current-host polling and host-id resolution in parallel."""
        loop = asyncio.get_running_loop()
        current_host_baseline: asyncio.Future[str | None] = loop.create_future()
        current_host_task = asyncio.create_task(
            self._wait_for_host_ready(
                self._host,
                current_host_baseline,
                timeout,
                poll_interval,
                retry,
            ),
        )
        host_names_task = asyncio.create_task(self._get_host_names_by_id())
        return current_host_baseline, current_host_task, host_names_task

    async def _resolve_restart_hosts(
        self,
        restart_timestamps: dict[str, str],
        host_names_task: asyncio.Task[dict[str, str]],
        current_host_task: asyncio.Task[None],
        current_host_baseline: asyncio.Future[str | None],
    ) -> dict[str, str]:
        """Resolve restart host ids to host names and publish current-host baseline."""
        try:
            host_names_by_id = await host_names_task
            restart_hosts_by_name = self._get_restart_hosts_by_name(
                restart_timestamps,
                host_names_by_id,
            )
            current_host_baseline.set_result(restart_hosts_by_name.get(self._host))
            return restart_hosts_by_name
        except Exception:
            current_host_task.cancel()
            raise

    @staticmethod
    def _get_restart_hosts_by_name(
        restart_timestamps: dict[str, str],
        host_names_by_id: dict[str, str],
    ) -> dict[str, str]:
        """Return restart baseline timestamps keyed by host name."""
        missing_host_ids = sorted(
            host_id
            for host_id in restart_timestamps
            if host_id not in host_names_by_id
        )
        if missing_host_ids:
            RestartWaiter._raise_missing_restart_hosts(missing_host_ids)

        return {
            host_names_by_id[host_id]: restart_timestamps[host_id]
            for host_id in restart_timestamps
        }

    async def _get_host_names_by_id(self) -> dict[str, str]:
        """Return MarkLogic host names keyed by host id."""
        async with AsyncClient(
            transport=RetryTransport(                                                                                                                                                                                   
                transport=AsyncHTTPTransport(verify=_SHARED_SSL_CONTEXT),
                retry=self._default_retry,
            ),
        ) as client:
            response = await client.get(
                f"{self._protocol}://{self._host}:{_MARKLOGIC_MANAGE_API_PORT}"
                f"{_HOSTS_ENDPOINT}",
                auth=self._auth,
                params={"format": "json"},
            )

        if response.status_code != httpx.codes.OK:
            return {}

        data = response.json()["host-default-list"]["list-items"]["list-item"]
        hosts = data if isinstance(data, list) else [data]
        return {
            host_info["idref"]: host_info["nameref"]
            for host_info in hosts
            if host_info.get("idref") and host_info.get("nameref")
        }

    async def _wait_for_host_ready(
        self,
        host: str,
        baseline_timestamp: _RestartTimestampBaseline,
        timeout: float,
        poll_interval: float,
        retry: Retry,
    ) -> None:
        """Wait for a single host to report readiness via the timestamp endpoint."""
        async with AsyncClient(
            headers={"Connection": "close"},
            timeout=5,
        ) as client:
            await self._poll_host_until_ready(
                client,
                host,
                baseline_timestamp,
                timeout,
                poll_interval,
                retry,
            )

    async def _poll_host_until_ready(
        self,
        client: AsyncClient,
        host: str,
        baseline_timestamp: _RestartTimestampBaseline,
        timeout: float,
        poll_interval: float,
        retry: Retry,
    ) -> None:
        """Poll one host until the timestamp endpoint confirms readiness."""
        deadline = time.monotonic() + timeout
        current_timestamp = ""

        while True:
            current_timestamp = await self._poll_host_once(
                client,
                host,
                current_timestamp,
                baseline_timestamp,
                deadline,
                retry,
            )
            if await self._is_ready_timestamp(current_timestamp, baseline_timestamp):
                return
            await asyncio.sleep(poll_interval)

    async def _poll_host_once(
        self,
        client: AsyncClient,
        host: str,
        current_timestamp: str,
        baseline_timestamp: _RestartTimestampBaseline,
        deadline: float,
        retry: Retry,
    ) -> str:
        """Perform a single timestamp probe for one host."""
        try:
            response = await client.get(
                self._get_timestamp_url(host),
                auth=self._auth,
            )
        except Exception as exc:
            if not retry.is_retryable_exception(exc):
                raise exc
            self._raise_wait_timeout_if_needed(
                host,
                baseline_timestamp,
                deadline,
                exc,
            )
            return current_timestamp

        if response.status_code == httpx.codes.OK:
            current_timestamp = response.text.strip()
            if await self._is_ready_timestamp(
                current_timestamp,
                baseline_timestamp,
                wait_for_pending_baseline=True,
            ):
                return current_timestamp
        elif not retry.is_retryable_status_code(response.status_code):
            self._raise_unexpected_timestamp_status(host, response.status_code)

        self._raise_wait_timeout_if_needed(
            host,
            baseline_timestamp,
            deadline,
        )
        return current_timestamp

    def _get_timestamp_url(self, host: str) -> str:
        """Return the Admin timestamp URL for a host."""
        return (
            f"{self._protocol}://{host}:{_MARKLOGIC_ADMIN_API_PORT}"
            f"{_RESTART_TIMESTAMP_PATH}"
        )

    async def _is_ready_timestamp(
        self,
        current_timestamp: str,
        baseline_timestamp: _RestartTimestampBaseline,
        wait_for_pending_baseline: bool = False,
    ) -> bool:
        """Return whether a timestamp proves host readiness."""
        if not current_timestamp:
            return False

        if (
            wait_for_pending_baseline
            and isinstance(baseline_timestamp, asyncio.Future)
            and not baseline_timestamp.done()
        ):
            await baseline_timestamp

        resolved_baseline = self._resolve_baseline_timestamp(baseline_timestamp)
        return resolved_baseline is None or current_timestamp != resolved_baseline

    @staticmethod
    def _resolve_baseline_timestamp(
        baseline_timestamp: _RestartTimestampBaseline,
    ) -> str | None:
        """Return the resolved baseline timestamp, if already available."""
        if isinstance(baseline_timestamp, asyncio.Future):
            if not baseline_timestamp.done():
                return None
            return baseline_timestamp.result()
        return baseline_timestamp

    def _raise_wait_timeout_if_needed(
        self,
        host: str,
        baseline_timestamp: _RestartTimestampBaseline,
        deadline: float,
        cause: Exception | None = None,
    ) -> None:
        """Raise a timeout once the wait deadline has passed."""
        if time.monotonic() < deadline:
            return
        self._raise_wait_timeout(
            host,
            self._resolve_baseline_timestamp(baseline_timestamp),
            cause,
        )

    @staticmethod
    def _raise_wait_timeout(
        host: str,
        previous_timestamp: str | None,
        cause: Exception | None = None,
    ) -> None:
        """Raise a timeout describing which host did not become ready."""
        timestamp_info = (
            f" after baseline timestamp [{previous_timestamp}]"
            if previous_timestamp
            else ""
        )
        msg = (
            f"Timed out waiting for MarkLogic host [{host}] to report readiness"
            f"{timestamp_info} via /admin/v1/timestamp."
        )
        if cause is not None:
            raise TimeoutError(msg) from cause
        raise TimeoutError(msg)

    @staticmethod
    def _raise_unexpected_timestamp_status(
        host: str,
        status_code: int,
    ) -> NoReturn:
        """Raise when the timestamp endpoint returns a non-retryable status."""
        msg = (
            "Expected /admin/v1/timestamp to return 200 OK, "
            f"got {status_code} for host [{host}]."
        )
        raise AssertionError(msg)

    @staticmethod
    def _raise_missing_restart_hosts(
        missing_host_ids: list[str],
    ) -> None:
        """Raise an error describing unresolved host ids from a restart payload."""
        msg = (
            "Could not resolve all restart host ids through /manage/v2/hosts. "
            f"Missing host ids: [{', '.join(missing_host_ids)}]"
        )
        raise ValueError(msg)
