from mlclient.xquery import cts


def run():
    return cts.field_words("field-names", forest_ids=None).compile()
