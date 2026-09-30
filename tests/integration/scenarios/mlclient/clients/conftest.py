from __future__ import annotations

import os
from uuid import uuid4

import pytest

from mlclient import MLClient
from mlclient.http import HTTPConfig
from mlclient.models import JSONDocument, Metadata, XMLDocument
from tests.utils import resources


def _create_database(ml: MLClient, name: str) -> None:
    spec = resources.get_test_resource_json(__file__, "database.json")
    ml.manage.databases.create({**spec, "database-name": name}).raise_for_status()


def _create_forest(ml: MLClient, name: str) -> None:
    host = ml.eval.xquery("xdmp:host-name(xdmp:host())")
    ml.manage.forests.create(
        {"forest-name": name, "host": host, "database": name},
    ).raise_for_status()


def _write_documents(ml: MLClient, database: str) -> None:
    metadata = Metadata(collections=["cts-test"])
    ml.documents.write(
        [
            XMLDocument(
                resources.read_test_resource_bytes(__file__, "documents/a.xml"),
                "/cts-test/a.xml",
                metadata,
            ),
            XMLDocument(
                resources.read_test_resource_bytes(__file__, "documents/b.xml"),
                "/cts-test/b.xml",
                metadata,
            ),
            JSONDocument(
                resources.get_test_resource_json(__file__, "documents/c.json"),
                "/cts-test/c.json",
                metadata,
            ),
        ],
        database=database,
    )


@pytest.fixture(scope="class")
def indexed_database():
    port = int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))
    manage_port = int(os.environ.get("MLCLIENT_CTS_MANAGE_PORT", "8002"))
    name = f"mlclient-cts-test-{uuid4().hex}"
    with MLClient(port=port, manage_config=HTTPConfig.resolve(port=manage_port)) as ml:
        _create_database(ml, name)
        try:
            _create_forest(ml, name)
            _write_documents(ml, name)
            yield ml, name, port
        finally:
            ml.manage.databases.delete(name, forest_delete="data").raise_for_status()
