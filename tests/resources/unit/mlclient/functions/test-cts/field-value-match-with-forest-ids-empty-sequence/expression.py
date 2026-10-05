from mlclient.functions.xqy import cts


def run():
    return cts.field_value_match("field-names", "prod*", forest_ids=None).compile()
