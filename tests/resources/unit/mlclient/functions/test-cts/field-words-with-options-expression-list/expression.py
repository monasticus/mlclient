from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_words(
        "field-names",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
