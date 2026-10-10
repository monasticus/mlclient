"""Public compilation and native serialization of SimilarQuery."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import FunctionCall, cts


def run():
    options = (
        '<options xmlns="cts:distinctive-terms"><!-- tuned --><m'
        "ax-terms>20</max-terms><?review later?></options>"
    )
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    assert query.to_json()["similarQuery"]["options"] == read_query_expectation(
        __file__,
        "expected-1.json",
    )
