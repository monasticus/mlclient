from mlclient.functions.xqy import cts


def run():
    return cts.field_values("field-names", start=2.5).compile()
