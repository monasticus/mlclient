from mlclient.functions.xqy import cts


def run():
    return cts.value_match(None, "prod*").compile()
