from mlclient.xquery import cts


def run():
    return cts.field_value_query("description", None).compile()
