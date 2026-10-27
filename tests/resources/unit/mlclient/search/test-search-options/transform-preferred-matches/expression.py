from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.TransformResults(
            preferred_matches=o.PreferredMatches(
                [s.Element("title"), s.Element("summary"), s.JsonProperty("title")],
            ),
            per_match_tokens=12,
            max_matches=2,
            max_snippet_chars=100,
        ),
    )
