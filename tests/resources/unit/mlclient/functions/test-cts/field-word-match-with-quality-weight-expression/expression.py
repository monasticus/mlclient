from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_word_match(
        "field-names", "prod*", quality_weight=fn.count(cts.search().index(1)),
    ).compile()
