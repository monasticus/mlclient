from __future__ import annotations

import asyncio
import shutil

import pytest

from mlclient.jobs import WriteDocumentsJob
from tests.utils import documents_client as docs_client_utils
from tests.utils import resources as resources_utils

TEST_RESOURCES_PATH = resources_utils.get_test_resources_path(__file__)
NUMBER_OF_DOCS = 1000


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    mimeo_config_path = resources_utils.get_test_resource_path(
        __file__,
        "mimeo-config.json",
    )
    output_path = f"{TEST_RESOURCES_PATH}/output"
    docs_configs = [
        (mimeo_config_path, output_path, NUMBER_OF_DOCS),
    ]
    docs_client_utils.generate_docs_with_mimeo(docs_configs)

    yield

    # Teardown
    shutil.rmtree(output_path)


def test_writing_docs_with_default_settings(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS)


def test_writing_docs_with_default_concurrency_batch_50(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=50)


def test_writing_docs_with_default_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=200)


def test_writing_docs_with_default_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=300)


def test_writing_docs_with_4_concurrency_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, concurrency=4)


def test_writing_docs_with_8_concurrency_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, concurrency=8)


def test_writing_docs_with_12_concurrency_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, concurrency=12)


def test_writing_docs_with_24_concurrency_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, concurrency=24)


def test_writing_docs_with_4_concurrency_batch_50(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=50,
    )


def test_writing_docs_with_8_concurrency_batch_50(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=50,
    )


def test_writing_docs_with_12_concurrency_batch_50(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=50,
    )


def test_writing_docs_with_24_concurrency_batch_50(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=50,
    )


def test_writing_docs_with_4_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=200,
    )


def test_writing_docs_with_8_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=200,
    )


def test_writing_docs_with_12_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=200,
    )


def test_writing_docs_with_24_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=200,
    )


def test_writing_docs_with_4_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=300,
    )


def test_writing_docs_with_8_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=300,
    )


def test_writing_docs_with_12_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=300,
    )


def test_writing_docs_with_24_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=300,
    )


def test_writing_docs_from_filesystem_with_default_settings(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        docs_path=f"{TEST_RESOURCES_PATH}/output",
    )


def _perform_parametrized_test(
    benchmark,
    docs_count: int,
    docs_path: str | None = None,
    concurrency: int | None = None,
    batch_size: int = 100,
):
    uri_prefix = "/perf-tests/write-job"
    uri_template = f"{uri_prefix}/doc-{{}}.xml"
    uris = [uri_template.format(i + 1) for i in range(docs_count)]

    try:
        docs_client_utils.assert_documents_do_not_exist(uris)

        if docs_path:
            job = benchmark(
                _write_job_with_filesystem_input,
                docs_path,
                uri_prefix,
                concurrency,
                batch_size,
            )
        else:
            job = benchmark(
                _write_job_with_documents_input,
                docs_count,
                uri_template,
                concurrency,
                batch_size,
            )

        assert job.report.completed == docs_count
        assert job.report.successful == docs_count
        assert job.report.failed == 0
        docs_client_utils.assert_documents_exist(uris)
    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)


def _write_job_with_documents_input(
    docs_count: int,
    uri_template: str,
    concurrency: int | None,
    batch_size: int,
):
    async def _run():
        docs = list(
            docs_client_utils.generate_docs(docs_count, uri_template=uri_template),
        )
        job = WriteDocumentsJob(concurrency=concurrency, batch_size=batch_size)
        job.with_client_config(port=8000, auth_method="digest")
        job.with_documents_input(docs)
        await job.run()
        return job

    return asyncio.run(_run())


def _write_job_with_filesystem_input(
    docs_path: str,
    uri_prefix: str,
    concurrency: int | None,
    batch_size: int,
):
    async def _run():
        job = WriteDocumentsJob(concurrency=concurrency, batch_size=batch_size)
        job.with_client_config(port=8000, auth_method="digest")
        job.with_filesystem_input(docs_path, uri_prefix=uri_prefix)
        await job.run()
        return job

    return asyncio.run(_run())
