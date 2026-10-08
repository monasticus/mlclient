from mlclient.xquery import cts, fn


def run():
    return cts.json_property_word_match(
        [fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))], "prod*",
    ).compile()
