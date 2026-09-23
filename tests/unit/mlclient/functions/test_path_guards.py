from __future__ import annotations

import pytest

from mlclient.functions.xqy import cts, fn
from mlclient.functions.xqy._expr import index_path, namespace_bindings


def test_all_nested_path_literals_are_bound_and_guarded():
    paths = ["/p:one", '/two[fn:contains(., "quote"&")]', "/a", "/b"]
    expr = fn.count([
        cts.search(paths[0]), cts.search(paths[1]),
        cts.uris(cts.path_range_query(paths[2:], "=", 3)),
    ])
    source, variables = expr.compile(namespaces={"p": "urn:one"})
    assert all(path in variables.values() for path in paths)
    assert all(path not in source for path in paths)
    assert source.count("cts:valid-extract-path(") == 2
    assert source.count("cts:valid-index-path(") == 2
    assert "MLCLIENT-INVALID-PATH" in source
    assert source.index("MLCLIENT-INVALID-PATH") < source.index("else xdmp:value")


@pytest.mark.parametrize("namespaces", [[], "p=urn:p", {1: "urn:p"}, {"p": 1}])
def test_namespace_binding_types(namespaces):
    with pytest.raises(TypeError, match="namespace"):
        cts.search("/p:item").compile(namespaces=namespaces)


@pytest.mark.parametrize("prefix", ["fn", "xs", "cts", "xdmp", "map", "xml", "xmlns"])
def test_compiler_namespaces_cannot_be_rebound(prefix):
    with pytest.raises(ValueError, match="reserved"):
        fn.count([]).compile(namespaces={prefix: "urn:override"})


def test_namespace_snapshot_and_empty_uri():
    original = {"": "urn:default", "p": "urn:p"}
    snapshot = namespace_bindings(original)
    original["p"] = "changed"
    assert snapshot == {"": "urn:default", "p": "urn:p"}
    with pytest.raises(ValueError, match="empty"):
        namespace_bindings({"p": ""})


def test_native_computed_index_arguments_remain_expressions():
    expr = fn.count([])
    assert index_path(expr) is expr


@pytest.mark.parametrize("prefix", ["p:x", "p; fn:error()", "two words", "1prefix"])
def test_invalid_namespace_prefix_cannot_enter_prolog(prefix):
    with pytest.raises(ValueError, match="NCName"):
        cts.search("/*").compile(namespaces={prefix: "urn:test"})


def test_namespace_declarations_escape_literals_and_allow_default_and_unicode():
    uri = 'urn:"; fn:error(); (: &quoted;\r\n'
    source, _ = fn.count([]).compile(
        namespaces={"p": uri, "": "urn:default", "ż": "urn:z"},
    )
    expected = 'declare namespace p = "urn:""; fn:error(); (: &amp;quoted;&#13;&#10;";'
    assert expected in source
    assert 'declare default element namespace "urn:default";' in source
    assert 'declare namespace ż = "urn:z";' in source
    assert "xdmp:value" not in source
    assert "xdmp:with-namespaces" not in source


def test_reference_namespace_map_is_snapshotted_and_used_for_validation():
    bindings = {"p": "urn:local"}
    expression = cts.path_reference("/p:item", namespaces=bindings)
    bindings["p"] = "changed"
    source, variables = expression.compile(namespaces={"p": "urn:global"})
    assert 'declare namespace p = "urn:global";' in source
    assert "urn:local" in variables.values()
    assert "changed" not in variables.values()
    assert "map:new((map:entry(" in source
    assert "cts:valid-index-path($v2, fn:true())" in source
