from mlclient.functions.xqy import cts


def run():
    return cts.field_words("field-names", forest_ids=[123]).compile()
