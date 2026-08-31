from __future__ import annotations

from time import sleep

import pytest

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError


@pytest.fixture(scope="class")
def ml_client():
    with MLClient() as ml:
        yield ml


class TestTransactions:
    TEST_DOC_URI = "/some/dir/txn-doc.xml"
    INSERT = f'xdmp:document-insert("{TEST_DOC_URI}", <root/>)'
    DOC_AVAILABLE = f'fn:doc-available("{TEST_DOC_URI}")'
    WRITE_DATABASE = "Modules"
    TRANSACTION_NAME = "mlclient-it-txn"

    @pytest.mark.ml_access
    def test_commit_makes_writes_visible(self, ml_client: MLClient):
        try:
            self._assert_not_visible(ml_client)
            with ml_client.transaction() as txn:
                self._write(ml_client, txn)
                self._assert_status_active(txn)
                self._assert_visible_in(ml_client, txn)
                self._assert_not_visible(ml_client)
            self._assert_status_gone(txn)
            self._assert_visible(ml_client)
        finally:
            self._delete(ml_client)

    @pytest.mark.ml_access
    def test_rollback_discards_writes(self, ml_client: MLClient):
        txn = ml_client.transaction()
        try:
            with pytest.raises(RuntimeError, match="boom"):
                self._write_then_fail(ml_client, txn)
            self._assert_status_gone(txn)
            self._assert_not_visible(ml_client)
        finally:
            self._delete(ml_client)

    @pytest.mark.ml_access
    def test_write_routes_to_transaction_database(self, ml_client: MLClient):
        write_db = self.WRITE_DATABASE
        try:
            with ml_client.transaction(database=write_db) as txn:
                assert txn.database == write_db
                self._write(ml_client, txn)
                self._assert_visible_in(ml_client, txn)
                self._assert_not_visible(ml_client, database=write_db)
                self._assert_not_visible(ml_client)
            self._assert_visible(ml_client, database=write_db)
            self._assert_not_visible(ml_client)
        finally:
            self._delete(ml_client, database=write_db)

    @pytest.mark.ml_access
    def test_time_limit_expires_transaction(self, ml_client: MLClient):
        try:
            txn = ml_client.transaction(time_limit=1)
            self._write(ml_client, txn)
            sleep(2)
            self._assert_status_gone(txn)
            with pytest.raises(MarkLogicError):
                txn.commit()
            self._assert_not_visible(ml_client)
        finally:
            self._delete(ml_client)

    @pytest.mark.ml_access
    def test_named_transaction_reported_in_status(self, ml_client: MLClient):
        with ml_client.transaction(name=self.TRANSACTION_NAME) as txn:
            status = txn.status()["transaction-status"]
            assert status["transaction-name"] == self.TRANSACTION_NAME

    @classmethod
    def _write_then_fail(cls, ml: MLClient, txn):
        with txn:
            cls._write(ml, txn)
            cls._assert_status_active(txn)
            cls._assert_visible_in(ml, txn)
            raise RuntimeError("boom")

    @classmethod
    def _write(cls, ml: MLClient, txn):
        ml.eval.xquery(cls.INSERT, **txn)

    @classmethod
    def _assert_visible_in(cls, ml: MLClient, txn):
        assert ml.eval.xquery(cls.DOC_AVAILABLE, **txn) is True

    @classmethod
    def _assert_visible(cls, ml: MLClient, database: str | None = None):
        assert ml.eval.xquery(cls.DOC_AVAILABLE, database=database) is True

    @classmethod
    def _assert_not_visible(cls, ml: MLClient, database: str | None = None):
        assert ml.eval.xquery(cls.DOC_AVAILABLE, database=database) is False

    @classmethod
    def _assert_status_active(cls, txn):
        status = txn.status()["transaction-status"]
        assert status["transaction-id"] == txn.id
        assert status["transaction-mode"] == "update"

    @classmethod
    def _assert_status_gone(cls, txn):
        with pytest.raises(MarkLogicError):
            txn.status()

    @classmethod
    def _delete(cls, ml: MLClient, database: str | None = None):
        if ml.eval.xquery(cls.DOC_AVAILABLE, database=database) is True:
            ml.eval.xquery(
                f'xdmp:document-delete("{cls.TEST_DOC_URI}")',
                database=database,
            )
