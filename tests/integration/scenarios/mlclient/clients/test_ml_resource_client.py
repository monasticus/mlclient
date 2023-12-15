from __future__ import annotations

from pytest_bdd import scenarios

from tests.integration.step_definitions import *

scenarios("../../../features/mlclient/clients/ml_resource_client.feature")
