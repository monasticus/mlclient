from mlclient.functions.xqy import cts


def run():
    return cts.registered_query(123).compile()
