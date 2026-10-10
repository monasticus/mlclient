import pytest
from mlclient.xquery import fn


def run():
    value = {}
    value["self"] = value
    with pytest.raises(ValueError, match="Circular"):
        fn.data(value)
