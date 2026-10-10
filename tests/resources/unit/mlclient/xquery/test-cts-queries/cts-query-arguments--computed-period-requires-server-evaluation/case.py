"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts, fn


def run():
    query = cts.period_range_query("valid", "aln_before", period=fn.doc("/p.xml"))
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:period-range-query: period: CTS period argument req"
        "uires server evaluation, got fn:doc('/p.xml')."
    )
