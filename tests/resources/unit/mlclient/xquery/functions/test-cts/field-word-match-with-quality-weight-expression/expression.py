from mlclient.xquery import cts, fn


def run():
    return cts.field_word_match(
        "field-names", "prod*", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
