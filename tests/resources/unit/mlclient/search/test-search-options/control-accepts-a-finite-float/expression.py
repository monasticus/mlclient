from mlclient.search.options import Control, SearchOptions


def run():
    return SearchOptions(Control("quality-weight", 0.5))
