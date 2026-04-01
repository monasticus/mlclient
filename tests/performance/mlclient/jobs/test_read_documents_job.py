from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from mlclient.jobs import ReadDocumentsJob, WriteDocumentsJob
from tests.utils import documents_client as docs_client_utils
from tests.utils import filesystem as fs_utils

TEST_OUTPUT_PATH = str(Path(__file__).resolve().parent / "output")
NUMBER_OF_DOCS = 10000


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    uri_prefix = "/perf-tests/read-job"
    uri_template = f"{uri_prefix}/doc-{{}}.xml"
    uris = [uri_template.format(i + 1) for i in range(NUMBER_OF_DOCS)]

    try:
        docs_client_utils.assert_documents_do_not_exist(uris)
        _write_job_with_documents_input(NUMBER_OF_DOCS, uri_template)
        docs_client_utils.assert_documents_exist(uris)

        yield

    finally:
        docs_client_utils.delete_documents(uris)
        docs_client_utils.assert_documents_do_not_exist(uris)


def test_reading_docs_with_default_settings(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS)


def test_reading_docs_with_default_concurrency_batch_100(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=100)


def test_reading_docs_with_default_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=200)


def test_reading_docs_with_default_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=300)


def test_reading_docs_with_default_concurrency_batch_500(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=500)


def test_reading_docs_with_default_concurrency_batch_600(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=600)


def test_reading_docs_with_default_concurrency_batch_700(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=700)


def test_reading_docs_with_default_concurrency_batch_800(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=800)


def test_reading_docs_with_default_concurrency_batch_900(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=900)


def test_reading_docs_with_default_concurrency_batch_1000(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=1000)


def test_reading_docs_with_4_concurrency_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, concurrency=4)


def test_reading_docs_with_8_concurrency_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, concurrency=8)


def test_reading_docs_with_12_concurrency_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, concurrency=12)


def test_reading_docs_with_24_concurrency_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, concurrency=24)


def test_reading_docs_with_4_concurrency_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=100,
    )


def test_reading_docs_with_8_concurrency_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=100,
    )


def test_reading_docs_with_12_concurrency_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=100,
    )


def test_reading_docs_with_24_concurrency_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=100,
    )


def test_reading_docs_with_4_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=200,
    )


def test_reading_docs_with_8_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=200,
    )


def test_reading_docs_with_12_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=200,
    )


def test_reading_docs_with_24_concurrency_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=200,
    )


def test_reading_docs_with_4_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=300,
    )


def test_reading_docs_with_8_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=300,
    )


def test_reading_docs_with_12_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=300,
    )


def test_reading_docs_with_24_concurrency_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=300,
    )


def test_reading_docs_with_4_concurrency_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=500,
    )


def test_reading_docs_with_8_concurrency_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=500,
    )


def test_reading_docs_with_12_concurrency_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=500,
    )


def test_reading_docs_with_24_concurrency_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=500,
    )


def test_reading_docs_with_4_concurrency_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=600,
    )


def test_reading_docs_with_8_concurrency_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=600,
    )


def test_reading_docs_with_12_concurrency_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=600,
    )


def test_reading_docs_with_24_concurrency_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=600,
    )


def test_reading_docs_with_4_concurrency_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=700,
    )


def test_reading_docs_with_8_concurrency_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=700,
    )


def test_reading_docs_with_12_concurrency_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=700,
    )


def test_reading_docs_with_24_concurrency_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=700,
    )


def test_reading_docs_with_4_concurrency_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=800,
    )


def test_reading_docs_with_8_concurrency_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=800,
    )


def test_reading_docs_with_12_concurrency_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=800,
    )


def test_reading_docs_with_24_concurrency_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=800,
    )


def test_reading_docs_with_4_concurrency_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=900,
    )


def test_reading_docs_with_8_concurrency_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=900,
    )


def test_reading_docs_with_12_concurrency_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=900,
    )


def test_reading_docs_with_24_concurrency_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=900,
    )


def test_reading_docs_with_4_concurrency_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=4,
        batch_size=1000,
    )


def test_reading_docs_with_8_concurrency_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=8,
        batch_size=1000,
    )


def test_reading_docs_with_12_concurrency_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=12,
        batch_size=1000,
    )


def test_reading_docs_with_24_concurrency_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        concurrency=24,
        batch_size=1000,
    )


def test_reading_docs_with_filesystem_output_and_default_settings(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        output_path=TEST_OUTPUT_PATH,
    )


def _perform_parametrized_test(
    benchmark,
    docs_count: int,
    concurrency: int | None = None,
    batch_size: int = 400,
    output_path: str | None = None,
):
    uri_prefix = "/perf-tests/read-job"
    uri_template = f"{uri_prefix}/doc-{{}}.xml"
    uris = [uri_template.format(i + 1) for i in range(docs_count)]

    if output_path:
        job = benchmark(
            _read_job_with_filesystem_output,
            uris,
            concurrency,
            batch_size,
            output_path,
        )
        fs_utils.safe_rmdir(output_path)
    else:
        job = benchmark(
            _read_job_with_documents_output,
            uris,
            concurrency,
            batch_size,
        )

    assert job.report.completed == docs_count
    assert job.report.successful == docs_count
    assert job.report.failed == 0


def _write_job_with_documents_input(
    docs_count: int,
    uri_template: str,
):
    docs = docs_client_utils.generate_docs(docs_count, uri_template=uri_template)
    job = WriteDocumentsJob()
    job.with_client_config(port=8000, auth_method="digest")
    job.with_documents_input(docs)
    job.run_sync()


def _read_job_with_documents_output(
    uris: list[str],
    concurrency: int | None,
    batch_size: int,
):
    async def _run():
        job = ReadDocumentsJob(concurrency=concurrency, batch_size=batch_size)
        job.with_client_config(port=8000, auth_method="digest")
        job.with_uris_input(uris)
        await job.run()
        return job

    return asyncio.run(_run())


def _read_job_with_filesystem_output(
    uris: list[str],
    concurrency: int | None,
    batch_size: int,
    output_path: str,
):
    async def _run():
        job = ReadDocumentsJob(concurrency=concurrency, batch_size=batch_size)
        job.with_client_config(port=8000, auth_method="digest")
        job.with_uris_input(uris)
        job.with_filesystem_output(output_path)
        await job.run()
        return job

    return asyncio.run(_run())
