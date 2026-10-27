from mlclient.search.options import CollectionConstraint, SearchOptions


def run():
    return SearchOptions(CollectionConstraint("type"))
