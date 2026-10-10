"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


@pytest.mark.parametrize(
    "build",
    [
        lambda index: SearchOptions().values("price", index),
        lambda index: SearchOptions().tuples("pair", index, index),
        lambda index: SearchOptions().range_constraint("price", index),
        lambda index: SearchOptions().sort(index),
    ],
    ids=["values", "tuples", "range-constraint", "sort"],
)
def run(build):
    calls = []

    class RecordingRange(Range):
        def to_json(self):
            calls.append("json")
            return super().to_json()

        def to_xml(self):
            calls.append("xml")
            return super().to_xml()

    options = build(RecordingRange(Element("price"), "xs:decimal"))
    assert calls == read_query_expectation(__file__, "expected-1.json")
    options.to_json()
    assert calls
    assert set(calls) == {"json"}
    calls.clear()
    options.to_xml()
    assert calls
    assert set(calls) == {"xml"}
