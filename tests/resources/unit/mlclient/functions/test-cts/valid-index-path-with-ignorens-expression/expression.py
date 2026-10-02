from mlclient.functions.xqy import cts, fn


def run():
    return cts.valid_index_path("/p:item", fn.exists(cts.search().pos(1))).compile()
