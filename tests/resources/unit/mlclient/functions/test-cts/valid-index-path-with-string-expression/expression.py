from mlclient.functions.xqy import cts, fn


def run():
    return cts.valid_index_path(fn.string(cts.search().index(1)), True).compile()
