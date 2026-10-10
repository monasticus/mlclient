"""Native proximity query serialization and compilation."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="repeat ordering or minimum-distance") as exc:
        cts.near_query([], options=["minimum-distance=1", "minimum-distance=2"])
    assert str(exc.value) == (
        "options ['minimum-distance=1', 'minimum-distance=2'] re"
        "peat ordering or minimum-distance"
    )
