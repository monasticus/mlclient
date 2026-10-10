"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import datetime
import pytest
from mlclient.xquery import cts


def run():
    query = cts.json_property_value_query("day", datetime.date(2026, 1, 1))
    with pytest.raises(ValueError, match="Unsupported local JSON") as error:
        query.serialize()
    assert str(error.value) == (
        "cts:json-property-value-query: value: Unsupported local"
        " JSON property value type: xs:date"
    )
