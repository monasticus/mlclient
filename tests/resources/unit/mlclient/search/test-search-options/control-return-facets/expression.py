from mlclient.search.options import Control, SearchOptions


def run():
    return SearchOptions(Control("return-facets", False))
