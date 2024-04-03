from __future__ import annotations

import logging
import shutil
from pathlib import Path

from mimeo import MimeoConfigFactory, Mimeograph

from mlclient import MLConfiguration, setup_logger
from mlclient.jobs import WriteDocumentsJob

_SCRIPT_DIR = Path(__file__).resolve().parent

##########################################
#             TO CUSTOMIZE               #
##########################################

ENV = "single"
# ENV = "cluster"
REST_SERVER = "manage"
DATABASE = "Documents"
# DATABASE = "App-Services"

##########################################

MIMEO_CONFIG_PATHS = [
    f"{_SCRIPT_DIR}/mimeo-configs/basic-xml.json",
    f"{_SCRIPT_DIR}/mimeo-configs/basic-json.json",
]
MIMEO_OUTPUT_ROOT = "output"
MIMEO_CUSTOM_COUNT = None
# MIMEO_CUSTOM_COUNT = 1000

##########################################


def generate_docs(
    mimeo_config_paths: list[str],
    custom_count: int | None = None,
):
    with Mimeograph() as mimeo:
        for mimeo_config_path in mimeo_config_paths:
            mimeo_config = MimeoConfigFactory.parse(mimeo_config_path)
            if custom_count:
                for template in mimeo_config.templates:
                    template.count = custom_count
            mimeo.submit((mimeo_config_path, mimeo_config))


def populate_database(
    env: str,
    rest_server_id: str,
    database: str | None,
    mimeo_output_root: str,
):
    ml_config = MLConfiguration.from_environment(env)
    client_config = ml_config.provide_config(rest_server_id)
    job = WriteDocumentsJob(batch_size=250)
    job.with_client_config(**client_config)
    job.with_database(database)
    job.with_filesystem_input(mimeo_output_root)
    job.start()
    job.await_completion()


setup_logger()
logging.getLogger("mlclient").setLevel(logging.DEBUG)

generate_docs(
    mimeo_config_paths=MIMEO_CONFIG_PATHS,
    custom_count=MIMEO_CUSTOM_COUNT,
)
populate_database(
    env=ENV,
    rest_server_id=REST_SERVER,
    database=DATABASE,
    mimeo_output_root=MIMEO_OUTPUT_ROOT,
)

shutil.rmtree(MIMEO_OUTPUT_ROOT)
