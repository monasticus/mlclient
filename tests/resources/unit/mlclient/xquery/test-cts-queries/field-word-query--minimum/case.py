from xml.etree.ElementTree import tostring

from mlclient.xquery import cts
from tests.utils.resources import read_query_expectation


def run():
    query = cts.field_word_query("title", "blue")
    assert query.to_json() == read_query_expectation(__file__, "expected.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected.xml",
    )
