from mlclient.xquery import cts


def run():
    return cts.field_words("field-names", quality_weight=2.5).compile()
