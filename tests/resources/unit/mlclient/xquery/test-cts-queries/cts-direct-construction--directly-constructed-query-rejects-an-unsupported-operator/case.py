"""CTS query classes normalize their arguments exactly like the cts builder."""

import pytest
from mlclient.xquery import ElementRangeQuery

NS = "http://example.com/ns"


def run():
    with pytest.raises(ValueError, match="unsupported range operator: 'gt'"):
        ElementRangeQuery("price", "gt", 10)
