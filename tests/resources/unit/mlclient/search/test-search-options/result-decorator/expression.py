from mlclient.search import options as o


def run():
    return o.SearchOptions(
        o.ResultDecorator(
            o.Callback("result", "https://example.com/search", "/search.xqy"),
        ),
    )
