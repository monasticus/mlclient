from xml.etree.ElementTree import ElementTree, fromstring, tostring
import pytest
from mlclient.xquery import SimilarQuery, ReverseQuery, cts


@pytest.mark.parametrize(
    "constructor",
    [cts.similar_query, cts.reverse_query, SimilarQuery, ReverseQuery],
)
def run(constructor):
    element = fromstring("<report>blue</report>")
    models = [{"label": "blue"}, element, ElementTree(element)]
    query = constructor(models)
    key = (
        "similarQuery"
        if constructor in (cts.similar_query, SimilarQuery)
        else "reverseQuery"
    )
    assert query.to_json() == {
        key: {
            "nodes": [
                {"label": "blue"},
                "<report>blue</report>",
                "<report>blue</report>",
            ],
        },
    }
    assert "<report>blue</report>" in tostring(query.to_xml(), encoding="unicode")
    models[0]["label"] = "changed"
    element.text = "changed"
    assert query.to_json()[key]["nodes"][0] == {"label": "blue"}
    assert query.to_json()[key]["nodes"][1] == "<report>blue</report>"
