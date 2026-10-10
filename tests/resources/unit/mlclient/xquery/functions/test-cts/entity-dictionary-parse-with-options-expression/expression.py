from mlclient.xquery import cts, fn


def run():
    return cts.entity_dictionary_parse(
        "contents", options=fn.string(cts.search().pos(1)),
    ).compile()
