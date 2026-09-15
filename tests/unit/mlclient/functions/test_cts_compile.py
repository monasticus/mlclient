from __future__ import annotations

import pytest

from mlclient.functions import cts, xs
from mlclient.functions.xqy._cts import _keyword
from mlclient.models.version import MarkLogicVersion
from mlclient.services import CtsService


def test_nested_query_parameterizes_every_value():
    query = cts.and_query(
        (cts.directory_query("/some/", "infinity"), cts.document_root("some")),
    )
    code, variables = query.compile()

    assert code == (
        "declare variable $v0 external;\n"
        "declare variable $v1 external;\n"
        'cts:and-query((cts:directory-query(($v0), "infinity"), '
        "cts:document-root-query(xs:QName($v1))))"
    )
    assert variables == {"v0": "/some/", "v1": "some"}


def test_no_user_value_is_interpolated_into_source():
    code, variables = cts.word_query('"); xdmp:document-delete("/x"').compile()

    assert '"); xdmp:document-delete' not in code
    assert variables == {"v0": '"); xdmp:document-delete("/x"'}


def test_typed_value_wrappers_carry_their_type():
    query = cts.element_range_query(xs.qname("price"), ">=", xs.integer(100))
    code, _ = query.compile()

    assert 'cts:element-range-query(xs:QName($v0), ">=", (xs:integer($v1)))' in code


def test_qname_with_namespace_uses_fn_qname():
    code, variables = cts.document_root(xs.qname("s", uri="urn:x")).compile()

    assert "fn:QName($v0, $v1)" in code
    assert variables == {"v0": "urn:x", "v1": "s"}


def test_invalid_range_operator_is_rejected():
    with pytest.raises(ValueError, match="range operator"):
        cts.element_range_query(xs.qname("p"), "=<", 1)


def test_trailing_empty_optionals_are_dropped():
    code, _ = cts.word_query("foo").compile()

    assert code.endswith("cts:word-query(($v0))")


def test_options_are_bound_as_strings():
    code, variables = cts.word_query("foo", options=["unstemmed"]).compile()

    assert "(xs:string($v1))" in code
    assert variables["v1"] == "unstemmed"


def test_keyword_rejects_embedded_quote():
    with pytest.raises(ValueError, match="must not contain a quote"):
        _keyword('x") or true(("')


def test_search_defaults_to_root_and_accepts_query_keyword():
    code, _ = cts.search(query=cts.true_query()).compile()

    assert code == "cts:search((/), cts:true-query())"


def test_search_rejects_paren_breakout_but_keeps_the_query_bound():
    breakout = '/, cts:false-query()), "unfiltered", ('
    with pytest.raises(ValueError, match="unbalanced search path"):
        cts.search(breakout, cts.true_query())


def test_search_allows_balanced_xpath_with_predicates_and_strings():
    code, _ = cts.search("/a/b[@id = 'x(1)']", cts.true_query()).compile()

    assert code == "cts:search((/a/b[@id = 'x(1)']), cts:true-query())"


def test_unwrapped_python_values_infer_their_type():
    code, variables = cts.element_range_query(xs.qname("n"), ">=", 100).compile()

    assert "xs:integer($v1)" in code
    assert variables["v1"] == 100


def test_service_shares_builder_api_and_evaluates_compiled_code():
    service = _fake_service()

    result = service.search("/", service.document_root("substance"))

    assert result == "ok"
    code = service._eval.calls[-1]
    assert "cts:search((/), cts:document-root-query(xs:QName($v0)))" in code["code"]
    assert code["variables"] == {"v0": "substance"}


def test_search_range_wraps_result_in_a_positional_predicate():
    service = _fake_service()

    service.search(query=service.true_query(), range=(11, 20))

    code = service._eval.calls[-1]["code"]
    assert code.endswith("(cts:search((/), cts:true-query()))[11 to 20]")


def test_search_range_integer_is_shorthand_for_the_first_n():
    service = _fake_service()

    service.search(query=service.true_query(), range=10)

    assert service._eval.calls[-1]["code"].endswith("[1 to 10]")


def test_search_range_with_invalid_bounds_is_rejected():
    service = _fake_service()

    with pytest.raises(ValueError, match="range bounds"):
        service.search(query=service.true_query(), range=(0, 5))


def test_service_rejects_functions_newer_than_its_version():
    service = _fake_service(version="10.0")

    with pytest.raises(ValueError, match="document-root-query requires MarkLogic 11"):
        service.search(query=service.document_root("substance"))

    assert service._eval.calls == []


def test_service_allows_functions_available_in_its_version():
    service = _fake_service(version="10.0")

    assert service.search(query=service.word_query("benzene")) == "ok"


class _FakeEval:
    def __init__(self):
        self.calls = []

    def xquery(self, code, *, variables):
        self.calls.append({"code": code, "variables": variables})
        return "ok"


def _fake_service(*, version="12.0"):
    service = CtsService.__new__(CtsService)
    service._eval = _FakeEval()
    service._version = MarkLogicVersion(version)
    return service
