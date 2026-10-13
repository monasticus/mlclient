from mlclient.search.options import SearchOptions


def run():
    return SearchOptions().collection_constraint("type")
