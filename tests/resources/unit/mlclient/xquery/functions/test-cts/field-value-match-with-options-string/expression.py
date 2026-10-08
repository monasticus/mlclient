from mlclient.xquery import cts


def run():
    return cts.field_value_match("field-names", "prod*", options="checked").compile()
