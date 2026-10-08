from mlclient.xquery import cts


def run():
    return cts.field_range_query("description", "=", 2.5).compile()
