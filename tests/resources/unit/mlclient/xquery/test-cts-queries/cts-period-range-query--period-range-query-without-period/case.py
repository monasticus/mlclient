"""Native ``cts:period-range-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
import datetime
from xml.etree.ElementTree import tostring
from mlclient.xquery import PeriodRangeQuery, cts

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
END = datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc)


def run():
    query = cts.period_range_query("valid", "aln_before")
    assert isinstance(query, PeriodRangeQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
