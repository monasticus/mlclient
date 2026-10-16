"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import opt


def run():
    return opt.options(
        opt.control("search-option", "unfiltered"),
        opt.control("search-option", "score-simple"),
    )
