"""Public compilation and native serialization of SimilarQuery."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    options = '<options xmlns="cts:distinctive-terms"><unknown>true</unknown></options>'
    query = cts.similar_query(
        None,
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    with pytest.raises(
        ValueError,
        match="Unsupported local CTS distinctive-term option",
    ) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:similar-query: options: Unsupported local CTS disti"
        "nctive-term option: {cts:distinctive-terms}unknown"
    )
