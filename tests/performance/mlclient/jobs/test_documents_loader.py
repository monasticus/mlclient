from __future__ import annotations

import shutil

import pytest
from mimeo import MimeoConfig, MimeoConfigFactory, Mimeograph

from mlclient.jobs import DocumentsLoader
from tests.utils import resources as resources_utils

TEST_RESOURCES_PATH = resources_utils.get_test_resources_path(__file__)


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    mimeo_configs = [
        _get_mimeo_config("output/output-5", 5),
        _get_mimeo_config("output/output-500", 500),
        _get_mimeo_config("output/output-15000", 15000),
        _get_mimeo_config("output/output-200000", 200000),
    ]

    with Mimeograph() as mimeo:
        for mimeo_config in mimeo_configs:
            config_id = f"config-{mimeo_config.templates[0].count}"
            mimeo.submit((config_id, mimeo_config))

    yield

    # Teardown
    output_path = f"{TEST_RESOURCES_PATH}/output"
    shutil.rmtree(output_path)


def test_load_5_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-5"
    benchmark(_load_documents, path)


def test_load_and_parse_5_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-5"
    benchmark(_load_documents, path, False)


def test_load_500_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-500"
    benchmark(_load_documents, path)


def test_load_and_parse_500_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-500"
    benchmark(_load_documents, path, False)


def test_load_15000_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-15000"
    benchmark(_load_documents, path)


def test_load_and_parse_15000_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-15000"
    benchmark(_load_documents, path, False)


def test_load_200000_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-200000"
    benchmark(_load_documents, path)


def test_load_and_parse_200000_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-200000"
    benchmark(_load_documents, path, False)


def _get_mimeo_config(
    output: str,
    count: int | None = None,
) -> MimeoConfig:
    config_path = resources_utils.get_test_resource_path(__file__, "mimeo-config.json")
    output_path = f"{TEST_RESOURCES_PATH}/{output}"

    mimeo_config = MimeoConfigFactory.parse(config_path)
    mimeo_config.output.directory_path = output_path
    if count:
        mimeo_config.templates[0].count = count
    return mimeo_config


def _load_documents(
    path: str,
    raw: bool = True,
):
    for doc in DocumentsLoader.load(path, "/test-documents", raw):
        assert doc.uri.startswith("/test-documents/")
