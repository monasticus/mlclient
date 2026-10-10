from mlclient.xquery import cts, fn


def run():
    return cts.word_match(
        "prod*",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
