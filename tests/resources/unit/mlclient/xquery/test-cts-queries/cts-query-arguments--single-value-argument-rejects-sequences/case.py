"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="exactly one value") as error:
        cts.document_format_query(["json", "xml"]).serialize()
    assert str(error.value) == (
        "cts:document-format-query: format: CTS argument require"
        "s exactly one value for local serialization."
    )
