"""Native ``cts:lsqt-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
import datetime
from xml.etree.ElementTree import tostring
from mlclient.xquery import LsqtQuery, cts

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def run():
    query = cts.lsqt_query("temporal", timestamp=START, options="cached", weight=2)
    assert isinstance(query, LsqtQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
