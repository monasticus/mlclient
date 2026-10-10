"""Native union query serialization and compilation."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="are not or-query options") as exc:
        cts.or_query([], options="ordered")
    assert (
        str(exc.value)
        == "options ['ordered'] are not or-query options; use at most one of synonym"
    )
