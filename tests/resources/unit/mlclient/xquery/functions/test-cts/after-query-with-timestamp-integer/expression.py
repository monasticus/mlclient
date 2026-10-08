from mlclient.xquery import cts


def run():
    return cts.after_query(123).compile()
