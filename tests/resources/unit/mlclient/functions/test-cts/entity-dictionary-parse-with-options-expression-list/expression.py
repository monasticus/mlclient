from mlclient.functions.xqy import cts, fn


def run():
    return cts.entity_dictionary_parse(
        "contents",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
