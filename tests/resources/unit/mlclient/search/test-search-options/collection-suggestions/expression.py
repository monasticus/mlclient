from mlclient.search import options as o


def run():
    return o.SearchOptions(
        o.SuggestionSource(
            o.Collection(
                prefix="https://example.com/tags/",
                facet=False,
                options="limit=4",
            ),
            ref="tags",
        ),
    )
