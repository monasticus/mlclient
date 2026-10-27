from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.Term(
            o.TermDefault(
                o.Value(
                    s.Element("item"),
                    attribute=s.Attribute("code"),
                    options="exact",
                    weight=2,
                ),
            ),
            callback=o.Callback("term", "https://example.com/search", "/search.xqy"),
        ),
    )
