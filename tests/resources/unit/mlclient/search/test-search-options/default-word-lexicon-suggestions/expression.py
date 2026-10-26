from mlclient.search import options as o


def run():
    return o.SearchOptions(
        o.DefaultSuggestionSource(
            o.WordLexicon("http://marklogic.com/collation/", "documents"),
            ref="title",
            options="limit=5",
        ),
    )
