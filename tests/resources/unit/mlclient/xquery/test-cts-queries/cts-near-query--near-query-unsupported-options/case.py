"""Native proximity query serialization and compilation."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="is not a near-query option") as exc:
        cts.near_query([], options="synonym")
    assert str(exc.value) == "option 'synonym' is not a near-query option"
