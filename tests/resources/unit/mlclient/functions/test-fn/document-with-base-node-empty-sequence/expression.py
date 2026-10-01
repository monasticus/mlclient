from mlclient.functions.xqy import cts, fn


def run():
    return fn.document(cts.search().index(1), base_node=None).compile()
