"""CTS query classes normalize their arguments exactly like the cts builder."""

import pytest
from mlclient.xquery import DirectoryQuery

NS = "http://example.com/ns"


def run():
    with pytest.raises(ValueError, match="directory depth must be '1' or 'infinity'"):
        DirectoryQuery("/a/", "2")
