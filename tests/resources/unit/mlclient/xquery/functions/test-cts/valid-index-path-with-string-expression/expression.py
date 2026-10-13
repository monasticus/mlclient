from mlclient.xquery import cts, fn


def run():
    return cts.valid_index_path(fn.string(cts.search().pos(1)), True).compile()
