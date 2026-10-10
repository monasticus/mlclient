"""Native ``cts:period-compare-query`` serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import PeriodCompareQuery, cts


def run():
    query = cts.period_compare_query(
        "system",
        "aln_equals",
        "valid",
        options="cached-incremental",
    )
    assert isinstance(query, PeriodCompareQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
