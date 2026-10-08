from mlclient.xquery import cts, fn


def run():
    return cts.percent_rank(
        "arg",
        "value",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
