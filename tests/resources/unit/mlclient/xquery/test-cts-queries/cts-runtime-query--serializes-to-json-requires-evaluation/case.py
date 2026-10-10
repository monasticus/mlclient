"""Runtime CTS queries compile but cannot be described without evaluation."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(TypeError) as error:
        cts.parse("blue").to_json()
    assert str(error.value) == (
        "runtime query: CTS runtime query requires server evalua"
        "tion before serialization."
    )
