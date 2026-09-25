from __future__ import annotations

import os
from uuid import uuid4

import pytest

from mlclient import MLClient
from mlclient.http import HTTPConfig


@pytest.fixture(scope="class")
def indexed_database():
    port = int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))
    manage_port = int(os.environ.get("MLCLIENT_CTS_MANAGE_PORT", "8002"))
    name = f"mlclient-cts-test-{uuid4().hex}"
    with MLClient(port=port, manage_config=HTTPConfig.resolve(port=manage_port)) as ml:
        ml.manage.databases.create(
            {
                "database-name": name,
                "uri-lexicon": True,
                "collection-lexicon": True,
                "geospatial-element-index": [
                    {
                        "namespace-uri": "https://monasticus.com/mlclient/examples/cts-test",
                        "localname": name,
                        "coordinate-system": "wgs84",
                        "point-format": "point",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    }
                    for name in ("origin", "destination")
                ],
                "path-namespace": [
                    {
                        "prefix": "t",
                        "namespace-uri": "https://monasticus.com/mlclient/examples/cts-test",
                    },
                ],
                "field": [
                    {
                        "field-name": "price",
                        "field-path": [{"path": "/t:item/t:price", "weight": 1.0}],
                    },
                ],
                "range-field-index": [
                    {
                        "scalar-type": "decimal",
                        "field-name": "price",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    },
                ],
                "range-path-index": [
                    {
                        "scalar-type": "decimal",
                        "path-expression": "/t:item/t:price",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    },
                ],
                "range-element-index": [
                    {
                        "scalar-type": "decimal",
                        "namespace-uri": "https://monasticus.com/mlclient/examples/cts-test",
                        "localname": "price",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    },
                    {
                        "scalar-type": "date",
                        "namespace-uri": "https://monasticus.com/mlclient/examples/cts-test",
                        "localname": "day",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    },
                ],
            },
        ).raise_for_status()
        try:
            host = ml.eval.xquery("xdmp:host-name(xdmp:host())")
            ml.manage.forests.create(
                {"forest-name": name, "host": host, "database": name},
            ).raise_for_status()
            ml.eval.xquery(
                """
                xdmp:document-insert("/cts-test/a.xml",
                    <item xmlns="https://monasticus.com/mlclient/examples/cts-test"><price>1.25</price>
                        <day>2026-01-01</day><label>alpha</label>
                        <origin>10,20</origin><destination>30,40</destination></item>,
                    (), "cts-test"),
                xdmp:document-insert("/cts-test/b.xml",
                    <item xmlns="https://monasticus.com/mlclient/examples/cts-test"><price>2.50</price>
                        <day>2026-01-02</day><label>beta</label></item>,
                    (), "cts-test"),
                xdmp:document-insert("/cts-test/c.json",
                    object-node {"active": true()}, (), "cts-test")
            """,
                database=name,
            )
            yield ml, name, port
        finally:
            ml.manage.databases.delete(name, forest_delete="data").raise_for_status()
