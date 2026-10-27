from mlclient.search import options as o


def run():
    return o.SearchOptions(
        o.ExtractDocumentData(
            ["/d:doc/d:title", "/d:doc/d:summary"],
            selected="include",
            namespaces={"d": "https://example.com/docs"},
        ),
    )
