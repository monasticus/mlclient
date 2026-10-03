from mlclient.functions.xqy import cts


def run():
    return cts.field_word_match("field-names", "prod*", quality_weight=2.5).compile()
