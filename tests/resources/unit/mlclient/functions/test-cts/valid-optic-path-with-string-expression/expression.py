from mlclient.functions.xqy import cts, fn


def run():
    return cts.valid_optic_path(fn.string(cts.search().index(1))).compile()
