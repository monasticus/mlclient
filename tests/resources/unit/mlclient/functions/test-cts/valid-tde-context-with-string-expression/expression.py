from mlclient.functions.xqy import cts, fn


def run():
    return cts.valid_tde_context(fn.string(cts.search().index(1))).compile()
