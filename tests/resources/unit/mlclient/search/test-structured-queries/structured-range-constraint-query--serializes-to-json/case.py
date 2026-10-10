from tests.utils.resources import read_query_expectation
from mlclient.search.structured import RangeConstraintQuery


def run():
    query = RangeConstraintQuery("price", [3, 4], operator="EQ", options=["cached"])
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
