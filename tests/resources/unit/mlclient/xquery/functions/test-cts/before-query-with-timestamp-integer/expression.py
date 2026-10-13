from mlclient.xquery import cts


def run():
    return cts.before_query(123).compile()
