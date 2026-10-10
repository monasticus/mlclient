"""Public compilation and native serialization of SimilarQuery."""

import pytest
from mlclient.xquery import cts, fn


def run():
    query = cts.similar_query(None, options=fn.doc("/options.xml"))
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:similar-query: options: CTS node argument requires "
        "a literal xdmp:unquote call or server evaluation."
    )
