from __future__ import annotations

import pytest

from mlclient.functions.xqy import cts, fn, xdmp, xs


def test_composed_namespaces_keep_the_entire_tree():
    code, variables = xs.string(
        fn.count(cts.values(cts.element_reference("price"))),
    ).compile()
    assert code.endswith(
        "xs:string(fn:count(cts:values(cts:element-reference(xs:QName($v0)))))",
    )
    assert variables == {"v0": "price"}
    assert str(xdmp.exists(cts.search(query=cts.true_query()))).endswith(
        "xdmp:exists(cts:search((/), cts:true-query()))",
    )
    code, bindings = xdmp.exists("/Q{urn:x}item").compile()
    assert "cts:valid-extract-path" in code
    assert "/Q{urn:x}item" in bindings.values()
    with pytest.raises(TypeError, match="path string"):
        xdmp.exists(42)


@pytest.mark.parametrize(
    ("value", "suffix"),
    [
        (None, "fn:count(())"),
        ([], "fn:count(())"),
        ((), "fn:count(())"),
        ("abc", "fn:count($v0)"),
        ([1, 2], "fn:count(($v0, $v1))"),
    ],
)
def test_uniform_sequence_semantics(value, suffix):
    assert str(fn.count(value)).endswith(suffix)
