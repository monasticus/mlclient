from mlclient.functions.xqy import cts


def run():
    return cts.field_value_match("field-names", 123).compile()
