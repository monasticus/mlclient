from mlclient.xquery import cts


def run():
    return cts.and_not_query(set(), "negative-query")
