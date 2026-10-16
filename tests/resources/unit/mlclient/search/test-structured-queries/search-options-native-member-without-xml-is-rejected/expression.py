"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import opt


def run():
    return opt.options(opt.native({"return-facets": False}))
