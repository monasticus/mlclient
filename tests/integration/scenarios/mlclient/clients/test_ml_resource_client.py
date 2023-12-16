from __future__ import annotations

from pytest_bdd import scenarios

scenarios("../../../features/mlclient/clients/ml_resource_client.feature")

pytest_plugins = [
    "tests.integration.step_definitions",
]
