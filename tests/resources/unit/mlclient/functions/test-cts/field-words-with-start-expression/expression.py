from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_words(
        "field-names", start=fn.string(cts.search().index(1)),
    ).compile()
