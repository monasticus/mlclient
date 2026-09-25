from __future__ import annotations

import pytest

from mlclient.functions.xqy import cts, xdmp


def test_exists_wraps_search_without_executing_it():
    assert xdmp.exists(cts.search(query=cts.true_query())).compile() == (
        'xquery version "1.0-ml";\nxdmp:exists(cts:search(/, cts:true-query()))',
        {},
    )


def test_exists_validates_a_literal_searchable_path():
    code, bindings = xdmp.exists(
        "/Q{https://monasticus.com/mlclient/examples/x}item",
    ).compile()
    assert "cts:valid-extract-path" in code
    assert "/Q{https://monasticus.com/mlclient/examples/x}item" in bindings.values()


def test_exists_rejects_a_non_path_argument():
    with pytest.raises(TypeError, match="path string"):
        xdmp.exists(42)
