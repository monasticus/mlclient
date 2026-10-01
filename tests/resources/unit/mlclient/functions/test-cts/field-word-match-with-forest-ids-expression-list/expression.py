from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_word_match(
        "field-names",
        "prod*",
        forest_ids=[fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
