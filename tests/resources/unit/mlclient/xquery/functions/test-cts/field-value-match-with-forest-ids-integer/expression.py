from mlclient.xquery import cts


def run():
    return cts.field_value_match("field-names", "prod*", forest_ids=123).compile()
