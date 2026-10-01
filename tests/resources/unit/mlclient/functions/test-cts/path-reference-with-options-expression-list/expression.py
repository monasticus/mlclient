from mlclient.functions.xqy import cts, fn


def run():
    return cts.path_reference(
        "/p:item",
        options=[fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
