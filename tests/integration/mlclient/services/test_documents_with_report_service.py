from __future__ import annotations

import pytest

from mlclient import AsyncMLClient
from mlclient.models import JSONDocument, XMLDocument
from mlclient.search import opt, sq

pytestmark = pytest.mark.ml_access
NS = "https://monasticus.com/mlclient/examples/cts-test"


class TestDocumentsWithReport:
    @pytest.mark.parametrize("category", [None, ["content", "metadata"], "metadata"])
    def test_page_and_document_categories(self, indexed_database, category):
        ml, database, _ = indexed_database
        report, documents = ml.search(
            database=database,
            collection="cts-test",
        ).documents_with_report(pos=[1, 3], category=category)

        assert report.total == 3
        assert report.start == 1
        assert report.page_length == 3
        assert report.effective_timestamp.isdigit()
        assert [doc.uri for doc in documents] == [hit["uri"] for hit in report.results]
        assert len(documents) == 3
        if category != "metadata":
            assert sum(type(doc) is XMLDocument for doc in documents) == 2
            assert sum(type(doc) is JSONDocument for doc in documents) == 1
        if category:
            assert all(doc.metadata.collections() == ["cts-test"] for doc in documents)

    def test_report_total_and_facets_cover_more_than_the_page(self, indexed_database):
        ml, database, _ = indexed_database
        options = opt.options(
            opt.range_constraint(
                "price",
                opt.range_(sq.element("price", NS), "xs:decimal"),
            ),
        )
        report, documents = ml.search(
            database=database,
            collection="cts-test",
            options=options,
        ).documents_with_report("alpha OR beta", pos=[2, 2])

        assert report.total == 2
        assert report.start == 2
        assert report.page_length == 1
        assert len(documents) == len(report.results) == 1
        assert documents[0].uri == report.results[0]["uri"]
        assert report.results[0]["score"] > 0
        assert report.facets["price"]["facetValues"] == [
            {"name": "1.25", "count": 1, "value": 1.25},
            {"name": "2.5", "count": 1, "value": 2.5},
        ]
        assert "total-time" in report.metrics

    def test_no_matches_still_returns_report(self, indexed_database):
        ml, database, _ = indexed_database
        report, documents = ml.search(database=database).documents_with_report(
            "missing-value",
            pos=[1, 2],
        )

        assert report.total == 0
        assert report.results == []
        assert report.response["qtext"] == "missing-value"
        assert report.effective_timestamp.isdigit()
        assert documents == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("category", [None, ["content", "metadata"], "metadata"])
    async def test_async_page_and_document_categories(self, indexed_database, category):
        _, database, port = indexed_database
        async with AsyncMLClient(port=port) as ml:
            report, documents = await ml.search(
                database=database,
                collection="cts-test",
            ).documents_with_report(pos=[1, 3], category=category)

        assert report.total == 3
        assert [doc.uri for doc in documents] == [hit["uri"] for hit in report.results]
        assert len(documents) == 3
        if category != "metadata":
            assert sum(type(doc) is XMLDocument for doc in documents) == 2
            assert sum(type(doc) is JSONDocument for doc in documents) == 1
        if category:
            assert all(doc.metadata.collections() == ["cts-test"] for doc in documents)

    @pytest.mark.asyncio
    async def test_async_no_matches_still_returns_report(self, indexed_database):
        _, database, port = indexed_database
        async with AsyncMLClient(port=port) as ml:
            search = ml.search(database=database)
            report, documents = await search.documents_with_report("missing-value")

        assert report.total == 0
        assert report.results == []
        assert documents == []
