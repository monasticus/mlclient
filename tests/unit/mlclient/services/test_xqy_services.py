from __future__ import annotations

import asyncio

import pytest

from mlclient.functions import cts
from mlclient.models.version import MarkLogicVersion
from mlclient.services import (
    AsyncCtsService,
    AsyncFnService,
    AsyncXdmpService,
    CtsService,
    FnService,
    XdmpService,
)


class _FakeEval:
    def __init__(self):
        self.calls = []

    def xquery(self, code, *, variables):
        self.calls.append({"code": code, "variables": variables})
        return "ok"


class _FakeAsyncEval:
    def __init__(self):
        self.calls = []

    async def xquery(self, code, *, variables):
        self.calls.append({"code": code, "variables": variables})
        return "ok"


def _sync(service_class):
    service = service_class.__new__(service_class)
    service._eval = _FakeEval()
    service._version = MarkLogicVersion("12.0")
    return service


def _async(service_class):
    service = service_class.__new__(service_class)
    service._eval = _FakeAsyncEval()
    service._version = MarkLogicVersion("12.0")
    return service


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        (None, "12.0"),
        ("11.0", "11.0"),
        (MarkLogicVersion("11.0"), "11.0"),
    ],
)
def test_service_coerces_its_target_version(version, expected):
    service = CtsService(object(), version=version)
    assert str(service._version) == expected


def test_async_service_defaults_to_the_latest_version():
    service = AsyncCtsService(object())
    assert str(service._version) == "12.0"


def test_sync_cts_uris_values_and_estimate_evaluate():
    service = _sync(CtsService)

    service.uris(service.true_query())
    service.values(service.element_reference("mf"))
    service.estimate(service.true_query())

    codes = [call["code"] for call in service._eval.calls]
    assert any("cts:uris(" in code for code in codes)
    assert any("cts:values(" in code for code in codes)
    assert any("cts:estimate(" in code for code in codes)


def test_sync_fn_and_xdmp_services_evaluate():
    fn_service = _sync(FnService)
    xdmp_service = _sync(XdmpService)

    fn_service.exists(cts.true_query())
    fn_service.empty(cts.true_query())
    xdmp_service.exists(cts.search("/x", cts.true_query()))

    assert "fn:exists(" in fn_service._eval.calls[0]["code"]
    assert "fn:empty(" in fn_service._eval.calls[1]["code"]
    assert "xdmp:exists(cts:search(" in xdmp_service._eval.calls[0]["code"]


def test_async_cts_service_evaluates_every_operation():
    service = _async(AsyncCtsService)

    async def run():
        await service.search(query=service.true_query())
        await service.uris(service.true_query())
        await service.values(service.element_reference("mf"))
        await service.estimate(service.true_query())

    asyncio.run(run())

    codes = [call["code"] for call in service._eval.calls]
    assert any("cts:search(" in code for code in codes)
    assert any("cts:uris(" in code for code in codes)
    assert any("cts:values(" in code for code in codes)
    assert any("cts:estimate(" in code for code in codes)


def test_async_fn_and_xdmp_services_evaluate():
    fn_service = _async(AsyncFnService)
    xdmp_service = _async(AsyncXdmpService)

    async def run():
        await fn_service.count(cts.true_query())
        await fn_service.exists(cts.true_query())
        await fn_service.empty(cts.true_query())
        await xdmp_service.exists("/x")

    asyncio.run(run())

    assert "fn:count(" in fn_service._eval.calls[0]["code"]
    assert "fn:exists(" in fn_service._eval.calls[1]["code"]
    assert "fn:empty(" in fn_service._eval.calls[2]["code"]
    assert "xdmp:exists(" in xdmp_service._eval.calls[0]["code"]
