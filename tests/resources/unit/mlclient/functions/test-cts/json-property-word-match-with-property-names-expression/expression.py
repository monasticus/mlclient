from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_word_match(
        fn.string(cts.search().pos(1)), "prod*",
    ).compile()
