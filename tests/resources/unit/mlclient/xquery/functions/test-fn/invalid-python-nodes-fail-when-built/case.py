from xml.etree.ElementTree import ElementTree
import pytest
from mlclient.xquery import fn


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ({1: "blue"}, TypeError),
        ({"nested": [{2: "blue"}]}, TypeError),
        ({"value": float("nan")}, ValueError),
        ({"value": float("inf")}, ValueError),
        ({"value": object()}, TypeError),
        (ElementTree(), ValueError),
    ],
)
def run(value, error):
    with pytest.raises(error):
        fn.data(value)
