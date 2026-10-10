"""Native proximity query serialization and compilation."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="is not a near-query option") as exc:
        cts.near_query([], options="minimum-distance=1.5")
    assert str(exc.value) == "option 'minimum-distance=1.5' is not a near-query option"
