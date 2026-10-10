"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="must be finite") as error:
        cts.element_geospatial_query("origin", cts.point(float("nan"), 0)).serialize()
    assert str(error.value) == (
        "cts:element-geospatial-query: region: CTS numbers must "
        "be finite for local serialization."
    )
