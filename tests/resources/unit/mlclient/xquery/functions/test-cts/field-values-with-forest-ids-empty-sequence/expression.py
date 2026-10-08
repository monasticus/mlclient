from mlclient.xquery import cts


def run():
    return cts.field_values("field-names", forest_ids=None).compile()
