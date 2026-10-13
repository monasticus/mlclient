from mlclient.xquery import cts


def run():
    return cts.not_in_query("positive-query", "negative-query").compile()
