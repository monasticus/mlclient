from mlclient.xquery import cts, fn


def run():
    return cts.linear_model(
        cts.search().pos(1), options=fn.string(cts.search().pos(1)),
    ).compile()
