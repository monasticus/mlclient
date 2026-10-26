from mlclient.search.options import Control, SearchOptions


def run():
    return SearchOptions(Control("page-length", 20))
