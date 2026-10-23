from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.DefaultSuggestionSource(
            o.WordLexicon("http://marklogic.com/collation/", "documents"),
            ref="title",
            options="limit=5",
        ),
        o.SuggestionSource(
            o.Word(s.Element("title"), options="case-insensitive"),
            ref="title",
        ),
        o.SuggestionSource(
            o.Collection(
                prefix="https://example.com/tags/",
                facet=False,
                options="limit=4",
            ),
            ref="tags",
        ),
        o.SuggestionSource(
            o.Range(s.Field("price"), "xs:decimal"),
            options=["ascending"],
            ref="prices",
        ),
    )
