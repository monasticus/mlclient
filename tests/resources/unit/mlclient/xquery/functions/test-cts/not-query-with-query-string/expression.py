from mlclient.xquery import cts


def run():
    return cts.not_query("needle").compile()
