"""Public compilation and native serialization of SimilarQuery."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.similar_query(
        None,
        options=FunctionCall("xdmp:unquote", ('{"maxTerms":20}',)),
    )
    with pytest.raises(ValueError, match="CTS similar options must be an XML") as error:
        query.serialize()
    assert str(error.value) == (
        "cts:similar-query: options: CTS similar options must be"
        " an XML cts:distinctive-terms options element."
    )
