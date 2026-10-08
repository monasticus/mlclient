from mlclient.xquery import cts, fn


def run():
    return cts.linear_model(
        cts.search().pos(1),
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
