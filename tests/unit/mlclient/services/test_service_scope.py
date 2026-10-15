"""Shared immutable defaults for document and evaluation services."""

from dataclasses import FrozenInstanceError

import pytest

from mlclient._options import UNSET
from mlclient.services import SearchScope, ServiceScope


def test_overridden_by_inherits_omitted_database():
    result = ServiceScope(database="catalog", txid="tx-1").overridden_by(
        ServiceScope(txid="tx-2"),
    )
    assert result == ServiceScope(database="catalog", txid="tx-2")


def test_overridden_by_inherits_omitted_transaction():
    result = ServiceScope(database="catalog", txid="tx-1").overridden_by(
        ServiceScope(database="archive"),
    )
    assert result == ServiceScope(database="archive", txid="tx-1")


def test_overridden_by_clears_database():
    result = ServiceScope(database="catalog", txid="tx-1").overridden_by(
        ServiceScope(database=None),
    )
    assert result == ServiceScope(database=None, txid="tx-1")


def test_overridden_by_clears_transaction():
    result = ServiceScope(database="catalog", txid="tx-1").overridden_by(
        ServiceScope(txid=None),
    )
    assert result == ServiceScope(database="catalog", txid=None)


def test_overridden_by_preserves_original():
    original = ServiceScope(database="catalog", txid="tx-1")
    original.overridden_by(ServiceScope(database="archive", txid="tx-2"))
    assert original == ServiceScope(database="catalog", txid="tx-1")


def test_overridden_by_none_returns_original():
    original = ServiceScope(database="catalog", txid="tx-1")
    assert original.overridden_by(None) is original


def test_overridden_by_rejects_search_scope():
    with pytest.raises(TypeError, match="scope must be a ServiceScope") as raised:
        ServiceScope().overridden_by(SearchScope(collection="products"))
    assert str(raised.value) == "scope must be a ServiceScope, got SearchScope"


def test_request_params_resolves_unset_fields():
    assert ServiceScope().request_params() == {"database": None, "txid": None}


def test_request_params_keeps_explicit_fields():
    assert ServiceScope(database="catalog", txid="tx-1").request_params() == {
        "database": "catalog",
        "txid": "tx-1",
    }


def test_request_params_keeps_explicit_none():
    assert ServiceScope(database=None, txid=None).request_params() == {
        "database": None,
        "txid": None,
    }


def test_request_params_preserves_unset_scope():
    scope = ServiceScope()
    scope.request_params()
    assert scope.database is UNSET
    assert scope.txid is UNSET


def test_scope_is_immutable():
    scope = ServiceScope(database="catalog")
    with pytest.raises(
        FrozenInstanceError, match="cannot assign to field 'database'",
    ) as raised:
        scope.database = "another"
    assert str(raised.value) == "cannot assign to field 'database'"
