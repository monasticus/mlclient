from mlclient.functions.xqy import cts


def run():
    return cts.field_word_match("field-names", "prod*", options=None).compile()
