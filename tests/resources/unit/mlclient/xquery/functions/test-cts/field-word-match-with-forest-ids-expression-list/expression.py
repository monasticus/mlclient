from mlclient.xquery import cts, fn


def run():
    return cts.field_word_match(
        "field-names",
        "prod*",
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
