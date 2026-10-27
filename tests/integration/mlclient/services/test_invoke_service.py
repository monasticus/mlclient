from __future__ import annotations

from uuid import uuid4

import pytest

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.models import TextDocument

ROOT = f"/mlclient-invoke-test/{uuid4().hex}"

WORDS_XQUERY = """xquery version "1.0-ml";
declare variable $word1 as xs:string external;
declare variable $word2 as xs:string external;
($word1, $word2, fn:concat($word1, " ", $word2))
"""
WORDS_JAVASCRIPT = 'xdmp.arrayValues([word1, word2, word1 + " " + word2])'
DATABASE_NAME_XQUERY = 'xquery version "1.0-ml"; xdmp:database-name(xdmp:database())'
INSERT_XQUERY = """xquery version "1.0-ml";
declare variable $uri as xs:string external;
xdmp:document-insert($uri, <invoked/>)
"""


@pytest.fixture(scope="class")
def ml_client():
    with MLClient() as ml:
        yield ml


@pytest.fixture(scope="class")
def modules_database(ml_client: MLClient):
    database = ml_client.eval.xquery("xdmp:database-name(xdmp:modules-database())")
    ml_client.documents.write(
        [
            TextDocument(WORDS_XQUERY, TestInvokeService.WORDS_XQUERY_MODULE),
            TextDocument(WORDS_JAVASCRIPT, TestInvokeService.WORDS_JAVASCRIPT_MODULE),
            TextDocument(DATABASE_NAME_XQUERY, TestInvokeService.DATABASE_NAME_MODULE),
            TextDocument(INSERT_XQUERY, TestInvokeService.INSERT_MODULE),
        ],
        database=database,
    )
    try:
        yield database
    finally:
        ml_client.documents.delete(TestInvokeService.MODULES, database=database)


@pytest.mark.usefixtures("modules_database")
class TestInvokeService:
    WORDS_XQUERY_MODULE = f"{ROOT}/words.xqy"
    WORDS_JAVASCRIPT_MODULE = f"{ROOT}/words.sjs"
    DATABASE_NAME_MODULE = f"{ROOT}/database-name.xqy"
    INSERT_MODULE = f"{ROOT}/insert.xqy"
    MODULES = (
        WORDS_XQUERY_MODULE,
        WORDS_JAVASCRIPT_MODULE,
        DATABASE_NAME_MODULE,
        INSERT_MODULE,
    )
    MISSING_MODULE = f"{ROOT}/missing.xqy"
    INSERTED_DOC_URI = f"{ROOT}/inserted.xml"

    @pytest.mark.ml_access
    def test_xquery_module_receives_variables(self, ml_client: MLClient):
        result = ml_client.invoke.module(
            self.WORDS_XQUERY_MODULE,
            word1="hello",
            word2="world",
        )

        assert result == ["hello", "world", "hello world"]

    @pytest.mark.ml_access
    def test_javascript_module_receives_variables(self, ml_client: MLClient):
        result = ml_client.invoke.module(
            self.WORDS_JAVASCRIPT_MODULE,
            variables={"word1": "hello", "word2": "world"},
        )

        assert result == ["hello", "world", "hello world"]

    @pytest.mark.ml_access
    def test_scoped_module_runs_against_scope_database(
        self,
        ml_client: MLClient,
        modules_database: str,
    ):
        scoped_invoke = ml_client.invoke(database=modules_database)

        assert scoped_invoke.module(self.DATABASE_NAME_MODULE) == modules_database

    @pytest.mark.ml_access
    def test_module_writes_within_transaction(self, ml_client: MLClient):
        try:
            with ml_client.transaction() as txn:
                ml_client.invoke.module(
                    self.INSERT_MODULE,
                    uri=self.INSERTED_DOC_URI,
                    **txn,
                )
                assert self._doc_available(ml_client, **txn) is True
                assert self._doc_available(ml_client) is False
            assert self._doc_available(ml_client) is True
        finally:
            ml_client.documents.delete(self.INSERTED_DOC_URI)

    @pytest.mark.ml_access
    def test_missing_module_raises_marklogic_error(self, ml_client: MLClient):
        with pytest.raises(MarkLogicError) as err:
            ml_client.invoke.module(self.MISSING_MODULE)

        expected_msg = (
            "XDMP-MODNOTFOUND: (err:XQST0059) "
            f"Module {self.MISSING_MODULE} not found\n"
            f"in {self.MISSING_MODULE} [1.0-ml]"
        )
        assert str(err.value) == expected_msg

    @classmethod
    def _doc_available(cls, ml: MLClient, **scope) -> bool:
        return ml.eval.xquery(
            "declare variable $uri external; fn:doc-available($uri)",
            uri=cls.INSERTED_DOC_URI,
            **scope,
        )
