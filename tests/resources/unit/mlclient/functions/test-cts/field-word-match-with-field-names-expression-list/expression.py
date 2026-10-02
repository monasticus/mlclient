from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_word_match(
        [fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))], "prod*",
    ).compile()
