from mlclient.xquery import cts, fn


def run():
    return cts.json_property_word_match(
        "price",
        "prod*",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
