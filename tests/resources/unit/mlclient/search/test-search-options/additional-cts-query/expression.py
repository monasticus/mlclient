from mlclient.search import options as o
from mlclient.xquery import cts


def run():
    return o.SearchOptions(o.AdditionalQuery(cts.collection_query("published")))
