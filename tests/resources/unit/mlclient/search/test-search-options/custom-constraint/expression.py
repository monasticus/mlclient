from mlclient.search import options as o


def run():
    return o.SearchOptions(
        o.CustomConstraint(
            "rating",
            o.Callback("parse", "https://example.com/search", "/rating.xqy"),
            facet=True,
            start_facet=o.Callback(
                "start",
                "https://example.com/search",
                "/rating.xqy",
            ),
            finish_facet=o.Callback(
                "finish",
                "https://example.com/search",
                "/rating.xqy",
            ),
            facet_options=["limit=5"],
            term_options=["case-insensitive"],
            annotation="Ratings",
        ),
    )
