from __future__ import annotations

import shutil

import pytest

from mlclient.io import DocumentsLoader
from tests.utils import documents_client as docs_client_utils
from tests.utils import resources as resources_utils

TEST_RESOURCES_PATH = resources_utils.get_test_resources_path(__file__)


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    for count in (5, 500, 15000, 200000):
        docs_client_utils.generate_document_files(
            f"{TEST_RESOURCES_PATH}/output/output-{count}",
            count,
        )

    yield

    # Teardown
    output_path = f"{TEST_RESOURCES_PATH}/output"
    shutil.rmtree(output_path)


def test_load_5_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-5"
    benchmark(_load_documents, path)


def test_load_500_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-500"
    benchmark(_load_documents, path)


def test_load_15000_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-15000"
    benchmark(_load_documents, path)


def test_load_200000_documents(benchmark):
    path = f"{TEST_RESOURCES_PATH}/output/output-200000"
    benchmark(_load_documents, path)


def _load_documents(
    path: str,
):
    for doc in DocumentsLoader.load(path, "/test-documents"):
        assert doc.uri.startswith("/test-documents/")
