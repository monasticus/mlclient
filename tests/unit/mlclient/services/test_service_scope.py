"""Shared service scopes route requests without changing the original service."""

from dataclasses import FrozenInstanceError

import pytest

from mlclient.services import SearchScope, ServiceScope


def test_scope_inherits_clears_and_remains_immutable():
    original = ServiceScope(database="catalog", txid="tx-1")
    inherited = original.overridden_by(ServiceScope(txid="tx-2"))
    assert inherited.request_params() == {"database": "catalog", "txid": "tx-2"}
    assert original.request_params() == {"database": "catalog", "txid": "tx-1"}
    assert original.overridden_by(ServiceScope(database=None)).request_params() == {
        "database": None,
        "txid": "tx-1",
    }
    assert ServiceScope().request_params() == {"database": None, "txid": None}
    assert original.overridden_by(None) is original
    with pytest.raises(FrozenInstanceError, match="cannot assign to field 'database'"):
        original.database = "another"


def test_rejects_search_scope_without_silently_dropping_filters():
    with pytest.raises(TypeError, match="scope must be a ServiceScope") as raised:
        ServiceScope().overridden_by(SearchScope(collection="products"))
    assert str(raised.value) == "scope must be a ServiceScope, got SearchScope"
