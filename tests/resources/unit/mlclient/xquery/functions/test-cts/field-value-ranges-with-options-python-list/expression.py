from mlclient.xquery import cts


def run():
    return cts.field_value_ranges("field-names", options=["checked"]).compile()
