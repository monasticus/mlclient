"""Native directory query serialization and compilation."""

import pytest
from mlclient.xquery import DirectoryQuery, xs


def run():
    with pytest.raises(ValueError, match="must be '1' or 'infinity'") as exc:
        DirectoryQuery("/reports/", xs.string("2")).serialize()
    assert (
        str(exc.value) == "cts:directory-query: depth ['2'] must be '1' or 'infinity'"
    )
