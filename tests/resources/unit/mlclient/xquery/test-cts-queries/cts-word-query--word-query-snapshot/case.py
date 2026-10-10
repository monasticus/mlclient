"""Native word-query serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import cts


def run():
    texts = ["blue"]
    query = cts.word_query(texts)
    texts.append("green")
    output = query.serialize()
    output["wordQuery"]["text"].append("red")
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
