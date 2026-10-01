from mlclient.functions.xqy import cts


def run():
    return cts.field_value_match("field-names", "prod*", query=None).compile()
