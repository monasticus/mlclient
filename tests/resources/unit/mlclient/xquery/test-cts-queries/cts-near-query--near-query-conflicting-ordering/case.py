"""Native proximity query serialization and compilation."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="repeat ordering or minimum-distance") as exc:
        cts.near_query([], options=["ordered", "unordered"])
    assert (
        str(exc.value)
        == "options ['ordered', 'unordered'] repeat ordering or minimum-distance"
    )
