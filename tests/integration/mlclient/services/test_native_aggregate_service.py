from __future__ import annotations

import os
import time
from decimal import Decimal

import pytest

from mlclient import AsyncMLClient
from mlclient.exceptions import MarkLogicError
from mlclient.models import ValueHit
from mlclient.search import opt
from mlclient.search.options import Range
from mlclient.search.structured import Element

pytestmark = pytest.mark.ml_access

NS = "https://monasticus.com/mlclient/examples/cts-test"
PLUGIN_PATH = "native/mlclient-test-aggregates"
RESULTS = [
    ("mean", "1.875"),
    ("label", "native aggregate"),
    (
        "summary",
        {
            "entry": {
                "key": "mean",
                "value": {
                    "type": "xs:double",
                    "_value": 1.875,
                },
            },
        },
    ),
    ("empty", None),
]


@pytest.fixture(scope="class")
def native_aggregate_plugin(indexed_database):
    """Install the test plugin ZIP from the local MarkLogic host filesystem."""
    package = os.environ.get("MLCLIENT_NATIVE_PLUGIN_ZIP")
    if not package:
        pytest.skip("Set MLCLIENT_NATIVE_PLUGIN_ZIP to the server-side test plugin ZIP")
    ml, database, _ = indexed_database
    ml.eval.xquery(
        'import module namespace plugin="http://marklogic.com/extension/plugin" '
        'at "/MarkLogic/plugin/plugin.xqy"; '
        "declare variable $package external; "
        'plugin:install-from-zip("native", xdmp:document-get($package)/node())',
        variables={"package": package},
    )
    # Plugin installation commits before its per-host library cache is populated.
    for attempt in range(30):
        try:
            ml.eval.xquery(
                'cts:aggregate("native/mlclient-test-aggregates", "empty", '
                f'cts:element-reference(fn:QName("{NS}", "price"), "type=decimal"))',
                database=database,
            )
            break
        except MarkLogicError as error:
            if "XDMP-NOLIBRARY:" not in str(error) or attempt == 29:
                raise
            time.sleep(0.1)
    return PLUGIN_PATH


class TestNativeAggregates:
    options = opt.options(
        opt.values("price", Range(Element("price", NS), "xs:decimal")),
    )

    def test_values_and_builtin_average(self, indexed_database):
        ml, database, _ = indexed_database
        prices = ml.search(database=database, options=self.options)

        assert prices.values("price", direction="descending") == [
            ValueHit(Decimal("2.5"), frequency=1),
            ValueHit(Decimal("1.25"), frequency=1),
        ]
        assert prices.values("price", "beta") == [
            ValueHit(Decimal("2.5"), frequency=1),
        ]
        assert prices.values("price", "missing-value") == []
        result = prices.aggregate("price", "avg")
        assert result == Decimal("1.875")
        assert type(result) is Decimal

    @pytest.mark.parametrize(("function", "expected"), RESULTS)
    def test_plugin_result(
        self,
        indexed_database,
        native_aggregate_plugin,
        function,
        expected,
    ):
        ml, database, _ = indexed_database
        prices = ml.search(database=database, options=self.options)

        result = prices.aggregate(
            "price",
            function,
            aggregate_path=native_aggregate_plugin,
        )

        assert result == expected
        assert type(result) is type(expected)
        assert (
            prices.aggregate(
                "price",
                function,
                "missing-value",
                aggregate_path=native_aggregate_plugin,
            )
            is None
        )

    def test_plugin_numeric_type_is_independent_of_lexicon(
        self,
        indexed_database,
        native_aggregate_plugin,
    ):
        ml, database, _ = indexed_database
        result = ml.eval.xquery(
            "declare variable $plugin external; "
            'cts:aggregate($plugin, "mean", '
            f'cts:element-reference(fn:QName("{NS}", "price"), "type=decimal"))',
            database=database,
            variables={"plugin": native_aggregate_plugin},
        )

        assert result == 1.875
        assert type(result) is float

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("function", "expected"), RESULTS)
    async def test_async_plugin_result(
        self,
        indexed_database,
        native_aggregate_plugin,
        function,
        expected,
    ):
        _, database, port = indexed_database
        async with AsyncMLClient(port=port) as ml:
            prices = ml.search(database=database, options=self.options)
            assert await prices.values("price", direction="descending") == [
                ValueHit(Decimal("2.5"), frequency=1),
                ValueHit(Decimal("1.25"), frequency=1),
            ]
            result = await prices.aggregate(
                "price",
                function,
                aggregate_path=native_aggregate_plugin,
            )
            assert result == expected
            assert type(result) is type(expected)
            assert (
                await prices.aggregate(
                    "price",
                    function,
                    "missing-value",
                    aggregate_path=native_aggregate_plugin,
                )
                is None
            )
