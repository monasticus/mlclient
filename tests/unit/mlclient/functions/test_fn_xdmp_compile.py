from __future__ import annotations

from mlclient.functions import cts, fn, xdmp
from mlclient.models.version import MarkLogicVersion
from mlclient.services import FnService, XdmpService


def test_fn_count_wraps_a_cts_values_expression():
    code, variables = fn.count(cts.values(cts.element_reference("mf"))).compile()

    assert code == (
        "declare variable $v0 external;\n"
        "fn:count(cts:values((cts:element-reference(xs:QName($v0))), ()))"
    )
    assert variables == {"v0": "mf"}


def test_xdmp_exists_wraps_a_cts_search_expression():
    code, _ = xdmp.exists(cts.search("/reaction", cts.true_query())).compile()

    assert code == "xdmp:exists(cts:search((/reaction), cts:true-query()))"


def test_xdmp_exists_accepts_a_bare_searchable_path():
    code, _ = xdmp.exists("/reaction/reaction-product/substance-uri").compile()

    assert code == "xdmp:exists((/reaction/reaction-product/substance-uri))"


def test_fn_service_evaluates_the_wrapped_expression():
    service = _fake_service(FnService)

    result = service.count(cts.values(cts.element_reference("mf")))

    assert result == "ok"
    assert service._eval.calls[-1]["code"].startswith("declare variable $v0")
    assert "fn:count(cts:values(" in service._eval.calls[-1]["code"]


def test_xdmp_service_evaluates_the_wrapped_expression():
    service = _fake_service(XdmpService)

    result = service.exists(cts.search("/reaction", cts.true_query()))

    assert result == "ok"
    assert service._eval.calls[-1]["code"].startswith("xdmp:exists(cts:search(")


class _FakeEval:
    def __init__(self):
        self.calls = []

    def xquery(self, code, *, variables):
        self.calls.append({"code": code, "variables": variables})
        return "ok"


def _fake_service(service_class, *, version="12.0"):
    service = service_class.__new__(service_class)
    service._eval = _FakeEval()
    service._version = MarkLogicVersion(version)
    return service
