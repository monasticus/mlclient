from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.Term(
            o.TermDefault(
                o.Word(
                    s.JsonProperty("title"),
                    options=["case-insensitive"],
                    fragment_scope="documents",
                    weight=1,
                ),
                ref="title",
            ),
            empty="no-results",
            options="unstemmed",
            fragment_scope="documents",
            weight=0.5,
        ),
    )
