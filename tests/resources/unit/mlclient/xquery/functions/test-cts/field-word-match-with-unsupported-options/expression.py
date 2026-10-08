from mlclient.xquery import cts


def run():
    return cts.field_word_match("field-names", "prod*", options=set())
