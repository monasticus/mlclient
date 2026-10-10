from mlclient.xquery import cts


def run():
    return cts.locks_fragment_query("needle").compile()
