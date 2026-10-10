"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(TypeError) as error:
        cts.element_geospatial_query("origin", cts.point("10,20")).serialize()
    assert str(error.value) == (
        "cts:element-geospatial-query: region: CTS point given a"
        "s WKT text requires server evaluation."
    )
