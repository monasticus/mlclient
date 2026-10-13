from mlclient.xquery import cts


def run():
    return cts.field_values("field-names", quality_weight=set())
