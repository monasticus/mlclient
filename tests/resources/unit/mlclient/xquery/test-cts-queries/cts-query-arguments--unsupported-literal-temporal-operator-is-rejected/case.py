"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts


@pytest.mark.parametrize(
    "build",
    [
        lambda: cts.period_compare_query("system", "bogus", "valid"),
        lambda: cts.period_range_query("valid", "bogus"),
    ],
)
def run(build):
    with pytest.raises(ValueError, match="temporal operator") as error:
        build()
    assert str(error.value) == "unsupported temporal operator: 'bogus'"
