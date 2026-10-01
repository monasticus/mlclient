from mlclient.functions.xqy import cts, fn


def run():
    return cts.directory_query(fn.string(cts.search().index(1))).compile()
