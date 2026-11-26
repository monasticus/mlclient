"""Each marked consumer error must continue to be rejected by mypy."""

from mlclient import MLClient, MLClientManager
from mlclient.services import CtsService


def rejected(client: MLClient, manager: MLClientManager) -> None:
    MLClient(retry="twice")  # error: arg-type
    manager.get_config("content", rety=2)  # error: call-arg
    CtsService(client.rest).uris(database=1)  # error: call-overload
    CtsService(client.rest).uris(output_type=int)  # error: arg-type
