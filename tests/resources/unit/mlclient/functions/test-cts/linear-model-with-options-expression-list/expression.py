from mlclient.functions.xqy import cts, fn


def run():
    return cts.linear_model(
        cts.search().pos(1),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
