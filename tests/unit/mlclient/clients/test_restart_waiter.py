from __future__ import annotations

import asyncio
import json

import httpx
import pytest
import respx
from httpx_retries import Retry
from pytest_mock import MockerFixture

from mlclient import (
    MARKLOGIC_ADMIN_API_PORT,
    MARKLOGIC_MANAGE_API_PORT,
    RESTART_RETRY_STRATEGY,
)
from mlclient.clients.restart_waiter import RestartWaiter
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

RESOURCES = resources_utils.get_test_resources(__file__)
TEXT_PLAIN = "text/plain; charset=UTF-8"
BASELINE_TS = "2026-03-16T11:06:25.657322+01:00"
READY_TS = "2026-03-16T11:06:41.608579+01:00"
NODE_B_BASELINE_TS = "2026-03-16T11:06:30.000000+01:00"
NODE_B_READY_TS = "2026-03-16T11:06:42.000000+01:00"
TEST_DEFAULT_RETRY = Retry(total=0)
FAST_TIMEOUT = 0.1
FAST_POLL_INTERVAL = 0.001
MULTIHOST_TIMEOUT = 0.5


def _admin_timestamp_url(host: str = "localhost") -> str:
    return f"http://{host}:{MARKLOGIC_ADMIN_API_PORT}/admin/v1/timestamp"


def _manage_hosts_url() -> str:
    return f"http://localhost:{MARKLOGIC_MANAGE_API_PORT}/manage/v2/hosts"


def _sequence_side_effect(*results: httpx.Response | Exception):
    iterator = iter(results)

    def side_effect(_request):
        result = next(iterator)
        if isinstance(result, Exception):
            raise result
        return result

    return side_effect


def _timestamp_response(
    timestamp: str = "",
    status_code: int = 200,
) -> httpx.Response:
    kwargs = {"status_code": status_code}
    if status_code == httpx.codes.OK:
        kwargs["text"] = timestamp
        kwargs["headers"] = {"Content-Type": TEXT_PLAIN}
    return httpx.Response(**kwargs)


def _mock_timestamp_route(
    mocker: MLRespXMocker,
    *responses: httpx.Response | Exception,
    host: str = "localhost",
):
    mocker.with_url(_admin_timestamp_url(host))
    if len(responses) == 1 and isinstance(responses[0], httpx.Response):
        response = responses[0]
        mocker.with_response_code(response.status_code)
        if response.headers.get("Content-Type"):
            mocker.with_response_content_type(response.headers["Content-Type"])
        if response.content:
            mocker.with_response_body(response.text)
        else:
            mocker.with_empty_response_body()
        return mocker.mock_get()
    return mocker.with_get_side_effect(_sequence_side_effect(*responses))


def _mock_hosts_lookup_from_resource(
    mocker: MLRespXMocker,
    resource_name: str,
):
    mocker.with_url(_manage_hosts_url())
    mocker.with_request_param("format", "json")
    mocker.with_response_code(200)
    mocker.with_response_body(RESOURCES[resource_name]["json"])
    return mocker.mock_get()


@pytest.fixture
def waiter() -> RestartWaiter:
    return RestartWaiter(
        protocol="http",
        host="localhost",
        auth=httpx.BasicAuth("admin", "admin"),
        default_retry=TEST_DEFAULT_RETRY,
    )


@pytest.fixture
def json_restart_response_factory():
    def build(
        last_startup: dict | list[dict],
        location: str = "/admin/v1/timestamp",
        content_type: str = "application/json; charset=UTF-8",
    ) -> httpx.Response:
        return httpx.Response(
            202,
            headers={
                "Location": location,
                "Content-Type": content_type,
            },
            content=json.dumps(
                {
                    "restart": {
                        "last-startup": last_startup,
                        "link": {
                            "kindref": "timestamp",
                            "uriref": location,
                        },
                        "message": "Check for new timestamp to verify host restart.",
                    },
                },
            ).encode(),
        )

    return build


@pytest.fixture
def xml_restart_response_factory():
    def build(
        body: bytes,
        location: str = "/admin/v1/timestamp",
    ) -> httpx.Response:
        return httpx.Response(
            202,
            headers={
                "Location": location,
                "Content-Type": "application/xml; charset=UTF-8",
            },
            content=body,
        )

    return build


@pytest.fixture
def ml_mocker() -> MLRespXMocker:
    return MLRespXMocker(use_router=False)


@pytest.fixture
def mocker_factory():
    def build() -> MLRespXMocker:
        return MLRespXMocker(use_router=False)

    return build


@respx.mock
def test_wait_for_restart_completion_without_restart_response(
    waiter: RestartWaiter,
    ml_mocker: MLRespXMocker,
):
    admin_route = _mock_timestamp_route(ml_mocker, _timestamp_response(READY_TS))

    waiter.wait_for_restart_completion(
        response=None,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 1


@respx.mock
def test_wait_for_restart_completion_waits_for_new_timestamp(
    mocker: MockerFixture,
    waiter: RestartWaiter,
    json_restart_response_factory,
    ml_mocker: MLRespXMocker,
):
    restart_response = json_restart_response_factory(
        {
            "host-id": "123",
            "value": BASELINE_TS,
        },
    )
    admin_route = _mock_timestamp_route(
        ml_mocker,
        _timestamp_response(BASELINE_TS),
        _timestamp_response(READY_TS),
    )
    sleep = mocker.patch(
        "mlclient.clients.restart_waiter.asyncio.sleep",
        new=mocker.AsyncMock(),
    )

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=MULTIHOST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 2
    sleep.assert_awaited_once()


@respx.mock
def test_wait_for_restart_completion_single_host_does_not_call_hosts_endpoint(
    waiter: RestartWaiter,
    json_restart_response_factory,
    ml_mocker: MLRespXMocker,
    mocker_factory,
):
    restart_response = json_restart_response_factory(
        {
            "host-id": "123",
            "value": BASELINE_TS,
        },
    )
    hosts_mocker = mocker_factory()
    hosts_route = _mock_hosts_lookup_from_resource(hosts_mocker, "empty-hosts.json")
    admin_route = _mock_timestamp_route(
        ml_mocker,
        _timestamp_response(BASELINE_TS),
        _timestamp_response(READY_TS),
    )

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=MULTIHOST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert hosts_route.call_count == 0
    assert admin_route.call_count == 2


@respx.mock
def test_wait_for_restart_completion_falls_back_to_current_host_when_resolution_fails(
    waiter: RestartWaiter,
    json_restart_response_factory,
    ml_mocker: MLRespXMocker,
    mocker_factory,
):
    restart_response = json_restart_response_factory(
        [
            {"host-id": "host-a", "value": BASELINE_TS},
            {"host-id": "host-b", "value": "2026-03-16T11:06:26.000000+01:00"},
        ],
    )
    _mock_hosts_lookup_from_resource(ml_mocker, "hosts-single-node-a.json")

    admin_mocker = mocker_factory()
    admin_route = _mock_timestamp_route(
        admin_mocker,
        _timestamp_response(READY_TS),
    )

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=MULTIHOST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 1


@respx.mock
def test_wait_for_restart_completion_waits_for_current_host_baseline_in_multihost_case(
    mocker: MockerFixture,
    waiter: RestartWaiter,
    json_restart_response_factory,
    mocker_factory,
):
    restart_response = json_restart_response_factory(
        [
            {
                "host-id": "localhost-id",
                "value": BASELINE_TS,
            },
            {
                "host-id": "node-b-id",
                "value": NODE_B_BASELINE_TS,
            },
        ],
    )
    hosts_mocker = mocker_factory()
    _mock_hosts_lookup_from_resource(
        hosts_mocker,
        "hosts-localhost-and-node-b.json",
    )

    current_host_mocker = mocker_factory()
    current_host_route = _mock_timestamp_route(
        current_host_mocker,
        _timestamp_response(BASELINE_TS),
        _timestamp_response(READY_TS),
    )

    node_b_mocker = mocker_factory()
    admin_route_b = _mock_timestamp_route(
        node_b_mocker,
        _timestamp_response(NODE_B_BASELINE_TS),
        _timestamp_response(NODE_B_READY_TS),
        host="node-b",
    )
    sleep = mocker.patch(
        "mlclient.clients.restart_waiter.asyncio.sleep",
        new=mocker.AsyncMock(),
    )

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=MULTIHOST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert current_host_route.call_count == 2
    assert admin_route_b.call_count == 2
    assert sleep.await_count >= 2


@respx.mock
def test_wait_for_restart_completion_waits_for_all_restart_hosts_in_parallel(
    mocker: MockerFixture,
    waiter: RestartWaiter,
    json_restart_response_factory,
    mocker_factory,
):
    restart_response = json_restart_response_factory(
        [
            {
                "host-id": "host-a-id",
                "value": BASELINE_TS,
            },
            {
                "host-id": "host-b-id",
                "value": NODE_B_BASELINE_TS,
            },
        ],
    )
    hosts_mocker = mocker_factory()
    _mock_hosts_lookup_from_resource(
        hosts_mocker,
        "hosts-node-a-and-node-b.json",
    )

    node_a_mocker = mocker_factory()
    admin_route_a = _mock_timestamp_route(
        node_a_mocker,
        _timestamp_response(BASELINE_TS),
        _timestamp_response(READY_TS),
        host="node-a",
    )
    node_b_mocker = mocker_factory()
    admin_route_b = _mock_timestamp_route(
        node_b_mocker,
        _timestamp_response(NODE_B_BASELINE_TS),
        _timestamp_response(NODE_B_READY_TS),
        host="node-b",
    )
    current_host_mocker = mocker_factory()
    current_host_route = _mock_timestamp_route(
        current_host_mocker,
        _timestamp_response("2026-03-16T11:06:50.000000+01:00"),
    )
    sleep = mocker.patch(
        "mlclient.clients.restart_waiter.asyncio.sleep",
        new=mocker.AsyncMock(),
    )

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=MULTIHOST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert current_host_route.call_count == 1
    assert admin_route_a.call_count == 2
    assert admin_route_b.call_count == 2
    assert sleep.await_count >= 2


def test_wait_for_restart_completion_raises_inside_running_loop(
    waiter: RestartWaiter,
):
    async def run():
        with pytest.raises(
            RuntimeError,
            match="running event loop",
        ):
            waiter.wait_for_restart_completion(
                response=None,
                timeout=FAST_TIMEOUT,
                poll_interval=FAST_POLL_INTERVAL,
                retry=RESTART_RETRY_STRATEGY,
            )

    asyncio.run(run())


@respx.mock
def test_wait_for_restart_completion_falls_back_when_hosts_endpoint_unavailable(
    waiter: RestartWaiter,
    json_restart_response_factory,
    ml_mocker: MLRespXMocker,
    mocker_factory,
):
    restart_response = json_restart_response_factory(
        [
            {"host-id": "host-a", "value": BASELINE_TS},
            {"host-id": "host-b", "value": "2026-03-16T11:06:26.000000+01:00"},
        ],
    )
    ml_mocker.with_url(_manage_hosts_url())
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()

    admin_mocker = mocker_factory()
    admin_route = _mock_timestamp_route(
        admin_mocker,
        _timestamp_response(READY_TS),
    )

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=MULTIHOST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 1


@respx.mock
def test_wait_for_restart_completion_raises_on_non_retryable_admin_status(
    waiter: RestartWaiter,
    ml_mocker: MLRespXMocker,
):
    ml_mocker.with_url(_admin_timestamp_url())
    ml_mocker.with_response_code(418)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()

    with pytest.raises(AssertionError, match="got 418"):
        waiter.wait_for_restart_completion(
            response=None,
            timeout=FAST_TIMEOUT,
            poll_interval=FAST_POLL_INTERVAL,
            retry=RESTART_RETRY_STRATEGY,
        )


@respx.mock
def test_wait_for_restart_completion_times_out_after_retryable_exception(
    waiter: RestartWaiter,
    ml_mocker: MLRespXMocker,
):
    ml_mocker.with_url(_admin_timestamp_url())
    ml_mocker.with_get_side_effect(httpx.ReadTimeout("timed out"))

    with pytest.raises(TimeoutError, match="localhost") as exc_info:
        waiter.wait_for_restart_completion(
            response=None,
            timeout=0.0,
            poll_interval=FAST_POLL_INTERVAL,
            retry=RESTART_RETRY_STRATEGY,
        )
    assert isinstance(exc_info.value.__cause__, httpx.ReadTimeout)


@respx.mock
def test_wait_for_restart_completion_retries_after_retryable_exception(
    mocker: MockerFixture,
    waiter: RestartWaiter,
    ml_mocker: MLRespXMocker,
):
    admin_route = _mock_timestamp_route(
        ml_mocker,
        httpx.ReadTimeout("timed out"),
        _timestamp_response(READY_TS),
    )
    sleep = mocker.patch(
        "mlclient.clients.restart_waiter.asyncio.sleep",
        new=mocker.AsyncMock(),
    )

    waiter.wait_for_restart_completion(
        response=None,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 2
    sleep.assert_awaited_once()


@respx.mock
def test_wait_for_restart_completion_retries_after_retryable_status(
    mocker: MockerFixture,
    waiter: RestartWaiter,
    ml_mocker: MLRespXMocker,
):
    admin_route = _mock_timestamp_route(
        ml_mocker,
        _timestamp_response(status_code=503),
        _timestamp_response(READY_TS),
    )
    sleep = mocker.patch(
        "mlclient.clients.restart_waiter.asyncio.sleep",
        new=mocker.AsyncMock(),
    )

    waiter.wait_for_restart_completion(
        response=None,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 2
    sleep.assert_awaited_once()


@respx.mock
def test_wait_for_restart_completion_times_out_after_stale_timestamp(
    waiter: RestartWaiter,
    json_restart_response_factory,
    ml_mocker: MLRespXMocker,
):
    restart_response = json_restart_response_factory(
        {
            "host-id": "123",
            "value": BASELINE_TS,
        },
    )
    _mock_timestamp_route(ml_mocker, _timestamp_response(BASELINE_TS))

    with pytest.raises(TimeoutError, match="baseline timestamp"):
        waiter.wait_for_restart_completion(
            restart_response,
            timeout=0.0,
            poll_interval=FAST_POLL_INTERVAL,
            retry=RESTART_RETRY_STRATEGY,
        )


@pytest.mark.parametrize(
    ("response", "expected_is_restart_response"),
    [
        (None, False),
        (
            httpx.Response(
                202,
                headers={"Location": "/admin/v1/timestamp"},
                content=b"",
            ),
            False,
        ),
        (
            httpx.Response(202, headers={"Location": "/other"}, content=b"{}"),
            False,
        ),
        (
            httpx.Response(
                202,
                headers={"Location": "/admin/v1/timestamp"},
                content=b"{}",
            ),
            True,
        ),
    ],
)
def test_is_restart_response(response, expected_is_restart_response):
    assert RestartWaiter.is_restart_response(response) is expected_is_restart_response


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(202, headers={"Location": "/admin/v1/timestamp"}, content=b""),
        httpx.Response(
            202,
            headers={
                "Location": "/admin/v1/timestamp",
                "Content-Type": "application/json",
            },
            content=b"{",
        ),
        httpx.Response(
            202,
            headers={
                "Location": "/admin/v1/timestamp",
                "Content-Type": "application/json",
            },
            json={"restart": []},
        ),
        httpx.Response(
            202,
            headers={
                "Location": "/admin/v1/timestamp",
                "Content-Type": "application/json",
            },
            json={
                "restart": {
                    "last-startup": {"host-id": "123", "value": "ts"},
                    "link": {"uriref": "/wrong/location"},
                },
            },
        ),
        httpx.Response(
            202,
            headers={
                "Location": "/admin/v1/timestamp",
                "Content-Type": "application/xml; charset=UTF-8",
            },
            content=b"<restart>",
        ),
        httpx.Response(
            202,
            headers={
                "Location": "/admin/v1/timestamp",
                "Content-Type": "application/xml; charset=UTF-8",
            },
            content=b"<ticket/>",
        ),
        httpx.Response(
            202,
            headers={
                "Location": "/admin/v1/timestamp",
                "Content-Type": "application/xml; charset=UTF-8",
            },
            content=(
                b"<restart><link><uriref>/wrong/location</uriref></link>"
                b"<last-startup host-id='1'>ts</last-startup></restart>"
            ),
        ),
    ],
)
@respx.mock
def test_wait_for_restart_treats_invalid_payloads_as_single_host_probe(
    waiter: RestartWaiter,
    ml_mocker: MLRespXMocker,
    response,
):
    admin_route = _mock_timestamp_route(ml_mocker, _timestamp_response(READY_TS))

    waiter.wait_for_restart_completion(
        response,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 1


@respx.mock
def test_wait_for_restart_completion_parses_valid_xml_restart_payload(
    waiter: RestartWaiter,
    xml_restart_response_factory,
    mocker: MockerFixture,
    mocker_factory,
):
    restart_response = xml_restart_response_factory(
        (
            b"<restart>"
            b"<link><uriref>/admin/v1/timestamp</uriref></link>"
            b"<last-startup host-id='host-a'>ts-a</last-startup>"
            b"<last-startup host-id='host-b'>ts-b</last-startup>"
            b"</restart>"
        ),
    )
    hosts_mocker = mocker_factory()
    _mock_hosts_lookup_from_resource(
        hosts_mocker,
        "hosts-node-a-and-node-b.xml-map.json",
    )

    current_host_mocker = mocker_factory()
    current_host_route = _mock_timestamp_route(
        current_host_mocker,
        _timestamp_response("current-host-ready-ts"),
    )
    node_a_mocker = mocker_factory()
    node_a_route = _mock_timestamp_route(
        node_a_mocker,
        _timestamp_response("ts-a"),
        _timestamp_response("node-a-ready-ts"),
        host="node-a",
    )
    node_b_mocker = mocker_factory()
    node_b_route = _mock_timestamp_route(
        node_b_mocker,
        _timestamp_response("ts-b"),
        _timestamp_response("node-b-ready-ts"),
        host="node-b",
    )
    sleep = mocker.patch(
        "mlclient.clients.restart_waiter.asyncio.sleep",
        new=mocker.AsyncMock(),
    )

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert current_host_route.call_count == 1
    assert node_a_route.call_count == 2
    assert node_b_route.call_count == 2
    assert sleep.await_count >= 2


@respx.mock
def test_wait_for_host_ready_returns_before_next_request_when_baseline_resolves(
    waiter: RestartWaiter,
    json_restart_response_factory,
    ml_mocker: MLRespXMocker,
):
    restart_response = json_restart_response_factory(
        {
            "host-id": "123",
            "value": "old-ts",
        },
    )

    def respond(_request):
        return _timestamp_response("new-ts")

    ml_mocker.with_url(_admin_timestamp_url())
    admin_route = ml_mocker.with_get_side_effect(respond)

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 1


@respx.mock
def test_wait_for_host_ready_returns_from_cached_timestamp_before_next_request(
    mocker: MockerFixture,
    waiter: RestartWaiter,
    json_restart_response_factory,
    ml_mocker: MLRespXMocker,
    mocker_factory,
):
    restart_response = json_restart_response_factory(
        [
            {
                "host-id": "localhost-id",
                "value": "old-ts",
            },
            {
                "host-id": "node-b-id",
                "value": "node-b-old-ts",
            },
        ],
    )
    real_sleep = asyncio.sleep
    state = {"current_host_called": False}

    async def resolve_hosts(_request):
        while not state["current_host_called"]:
            await real_sleep(FAST_POLL_INTERVAL)
        return httpx.Response(
            200,
            json=RESOURCES["hosts-localhost-and-node-b-delayed.json"]["json"],
        )

    sleep = mocker.patch(
        "mlclient.clients.restart_waiter.asyncio.sleep",
        new=mocker.AsyncMock(),
    )
    hosts_mocker = mocker_factory()
    hosts_mocker.with_url(_manage_hosts_url())
    hosts_mocker.with_request_param("format", "json")
    hosts_route = hosts_mocker.with_get_side_effect(resolve_hosts)

    node_b_mocker = mocker_factory()
    node_b_route = _mock_timestamp_route(
        node_b_mocker,
        _timestamp_response("node-b-old-ts"),
        _timestamp_response("node-b-new-ts"),
        host="node-b",
    )

    def respond_current_host(_request):
        state["current_host_called"] = True
        return _timestamp_response("new-ts")

    ml_mocker.with_url(_admin_timestamp_url())
    admin_route = ml_mocker.with_get_side_effect(respond_current_host)

    waiter.wait_for_restart_completion(
        restart_response,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 1
    assert hosts_route.call_count == 1
    assert node_b_route.call_count == 2
    sleep.assert_awaited()


@respx.mock
def test_wait_for_restart_completion_times_out_while_current_host_baseline_is_pending(
    waiter: RestartWaiter,
    json_restart_response_factory,
    mocker_factory,
):
    restart_response = json_restart_response_factory(
        [
            {"host-id": "localhost-id", "value": BASELINE_TS},
            {"host-id": "node-b-id", "value": NODE_B_BASELINE_TS},
        ],
    )
    real_sleep = asyncio.sleep

    async def resolve_hosts(_request):
        await real_sleep(FAST_POLL_INTERVAL)
        return httpx.Response(
            200,
            json=RESOURCES["hosts-localhost-and-node-b-delayed.json"]["json"],
        )

    hosts_mocker = mocker_factory()
    hosts_mocker.with_url(_manage_hosts_url())
    hosts_mocker.with_request_param("format", "json")
    hosts_mocker.with_get_side_effect(resolve_hosts)

    current_host_mocker = mocker_factory()
    current_host_route = _mock_timestamp_route(
        current_host_mocker,
        httpx.ReadTimeout("timed out"),
    )

    with pytest.raises(TimeoutError, match="localhost"):
        waiter.wait_for_restart_completion(
            restart_response,
            timeout=0.0,
            poll_interval=FAST_POLL_INTERVAL,
            retry=RESTART_RETRY_STRATEGY,
        )

    assert current_host_route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_wait_for_restart_completion_without_restart_response(
    waiter: RestartWaiter,
):
    ml_mocker = MLRespXMocker(use_router=False)
    admin_route = _mock_timestamp_route(ml_mocker, _timestamp_response(READY_TS))

    await waiter.async_wait_for_restart_completion(
        response=None,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_wait_for_restart_completion_waits_for_new_timestamp(
    mocker: MockerFixture,
    waiter: RestartWaiter,
    json_restart_response_factory,
):
    ml_mocker = MLRespXMocker(use_router=False)
    restart_response = json_restart_response_factory(
        {
            "host-id": "123",
            "value": BASELINE_TS,
        },
    )
    admin_route = _mock_timestamp_route(
        ml_mocker,
        _timestamp_response(BASELINE_TS),
        _timestamp_response(READY_TS),
    )
    sleep = mocker.patch(
        "mlclient.clients.restart_waiter.asyncio.sleep",
        new=mocker.AsyncMock(),
    )

    await waiter.async_wait_for_restart_completion(
        restart_response,
        timeout=MULTIHOST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    assert admin_route.call_count == 2
    sleep.assert_awaited_once()


@respx.mock
def test_wait_for_restart_completion_uses_custom_probe_timeout(
    mocker: MockerFixture,
    ml_mocker: MLRespXMocker,
):
    custom_timeout = 42.0
    waiter = RestartWaiter(
        protocol="http",
        host="localhost",
        auth=httpx.BasicAuth("admin", "admin"),
        default_retry=TEST_DEFAULT_RETRY,
        probe_timeout=custom_timeout,
    )
    _mock_timestamp_route(ml_mocker, _timestamp_response(READY_TS))
    async_client_cls = mocker.patch(
        "mlclient.clients.restart_waiter.AsyncClient",
        wraps=httpx.AsyncClient,
    )

    waiter.wait_for_restart_completion(
        response=None,
        timeout=FAST_TIMEOUT,
        poll_interval=FAST_POLL_INTERVAL,
        retry=RESTART_RETRY_STRATEGY,
    )

    async_client_cls.assert_called_once_with(
        transport=mocker.ANY,
        headers={"Connection": "close"},
        timeout=custom_timeout,
    )
