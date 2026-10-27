from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.SuggestionSource(
            o.Word(s.Element("title"), options="case-insensitive"),
            ref="title",
        ),
    )
