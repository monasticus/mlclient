from mlclient.search import options as o
from mlclient.xquery import cts


def run():
    return o.SearchOptions(
        o.Grammar(implicit=o.Implicit(cts.or_query([]), options="unordered")),
    )
