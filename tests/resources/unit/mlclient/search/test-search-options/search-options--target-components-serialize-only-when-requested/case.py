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
        lambda target: SearchOptions().word_constraint("label", target),
        lambda target: SearchOptions().value_constraint("label", target),
        lambda target: SearchOptions().container_constraint("label", target),
    ],
    ids=["word-constraint", "value-constraint", "container-constraint"],
)
def run(build):
    calls = []

    class RecordingElement(Element):
        def to_json(self):
            calls.append("json")
            return super().to_json()

        def to_xml(self):
            calls.append("xml")
            return super().to_xml()

    options = build(RecordingElement("label"))
    assert calls == read_query_expectation(__file__, "expected-1.json")
    options.to_json()
    assert calls == read_query_expectation(__file__, "expected-2.json")
    calls.clear()
    options.to_xml()
    assert calls == read_query_expectation(__file__, "expected-3.json")
