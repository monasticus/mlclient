from mlclient.functions.xqy import cts


def run():
    return cts.words(query="needle").compile()
