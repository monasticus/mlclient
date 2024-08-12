from __future__ import annotations

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
    uri_prefix = "/performance-tests/read-documents-job"
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


def test_reading_docs_with_default_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=100)


def test_reading_docs_with_default_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=200)


def test_reading_docs_with_default_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=300)


def test_reading_docs_with_default_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=500)


def test_reading_docs_with_default_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=600)


def test_reading_docs_with_default_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=700)


def test_reading_docs_with_default_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=800)


def test_reading_docs_with_default_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=900)


def test_reading_docs_with_default_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, batch_size=1000)


def test_reading_docs_with_4_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, thread_count=4)


def test_reading_docs_with_8_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, thread_count=8)


def test_reading_docs_with_12_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, thread_count=12)


def test_reading_docs_with_24_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(benchmark, docs_count=NUMBER_OF_DOCS, thread_count=24)


def test_reading_docs_with_4_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=100,
    )


def test_reading_docs_with_8_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=100,
    )


def test_reading_docs_with_12_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=100,
    )


def test_reading_docs_with_24_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=100,
    )


def test_reading_docs_with_4_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=200,
    )


def test_reading_docs_with_8_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=200,
    )


def test_reading_docs_with_12_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=200,
    )


def test_reading_docs_with_24_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=200,
    )


def test_reading_docs_with_4_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=300,
    )


def test_reading_docs_with_8_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=300,
    )


def test_reading_docs_with_12_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=300,
    )


def test_reading_docs_with_24_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=300,
    )


def test_reading_docs_with_4_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=500,
    )


def test_reading_docs_with_8_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=500,
    )


def test_reading_docs_with_12_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=500,
    )


def test_reading_docs_with_24_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=500,
    )


def test_reading_docs_with_4_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=600,
    )


def test_reading_docs_with_8_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=600,
    )


def test_reading_docs_with_12_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=600,
    )


def test_reading_docs_with_24_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=600,
    )


def test_reading_docs_with_4_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=700,
    )


def test_reading_docs_with_8_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=700,
    )


def test_reading_docs_with_12_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=700,
    )


def test_reading_docs_with_24_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=700,
    )


def test_reading_docs_with_4_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=800,
    )


def test_reading_docs_with_8_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=800,
    )


def test_reading_docs_with_12_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=800,
    )


def test_reading_docs_with_24_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=800,
    )


def test_reading_docs_with_4_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=900,
    )


def test_reading_docs_with_8_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=900,
    )


def test_reading_docs_with_12_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=900,
    )


def test_reading_docs_with_24_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=900,
    )


def test_reading_docs_with_4_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=1000,
    )


def test_reading_docs_with_8_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=1000,
    )


def test_reading_docs_with_12_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=1000,
    )


def test_reading_docs_with_24_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
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


def test_reading_docs_with_filesystem_output_and_default_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=100,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_default_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=200,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_default_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=300,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_default_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=500,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_default_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=600,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_default_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=700,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_default_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=800,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_default_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=900,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_default_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        batch_size=1000,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_default_batch(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=100,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=100,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=100,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_100(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=100,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=200,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=200,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=200,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_200(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=200,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=300,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=300,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=300,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_300(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=300,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=500,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=500,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=500,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_500(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=500,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=600,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=600,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=600,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_600(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=600,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=700,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=700,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=700,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_700(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=700,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=800,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=800,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=800,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_800(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=800,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=900,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=900,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=900,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_900(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=900,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_4_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=4,
        batch_size=1000,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_8_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=8,
        batch_size=1000,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_12_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=12,
        batch_size=1000,
        output_path=TEST_OUTPUT_PATH,
    )


def test_reading_docs_with_filesystem_output_and_24_threads_batch_1000(
    benchmark,
):
    _perform_parametrized_test(
        benchmark,
        docs_count=NUMBER_OF_DOCS,
        thread_count=24,
        batch_size=1000,
        output_path=TEST_OUTPUT_PATH,
    )


def _perform_parametrized_test(
    benchmark,
    docs_count: int,
    thread_count: int | None = None,
    batch_size: int = 400,
    output_path: str | None = None,
):
    uri_prefix = "/performance-tests/read-documents-job"
    uri_template = f"{uri_prefix}/doc-{{}}.xml"
    uris = [uri_template.format(i + 1) for i in range(docs_count)]

    if output_path:
        job = benchmark(
            _read_job_with_filesystem_output,
            uris,
            thread_count,
            batch_size,
            output_path,
        )
        fs_utils.safe_rmdir(output_path)
    else:
        job = benchmark(
            _read_job_with_documents_output,
            uris,
            thread_count,
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
    job.with_client_config(auth_method="digest")
    job.with_documents_input(docs)
    job.start()
    job.await_completion()


def _read_job_with_documents_output(
    uris: list[str],
    thread_count: int | None,
    batch_size: int,
):
    job = ReadDocumentsJob(thread_count=thread_count, batch_size=batch_size)
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.start()
    job.await_completion()

    return job


def _read_job_with_filesystem_output(
    uris: list[str],
    thread_count: int | None,
    batch_size: int,
    output_path: str,
):
    job = ReadDocumentsJob(thread_count=thread_count, batch_size=batch_size)
    job.with_client_config(auth_method="digest")
    job.with_uris_input(uris)
    job.with_filesystem_output(output_path)
    job.start()
    job.await_completion()

    return job
