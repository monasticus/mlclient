from mlclient.xquery import cts


def run():
    return cts.registered_query(None).compile()
