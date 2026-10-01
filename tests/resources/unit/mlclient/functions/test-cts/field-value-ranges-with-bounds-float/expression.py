from mlclient.functions.xqy import cts


def run():
    return cts.field_value_ranges("field-names", bounds=2.5).compile()
