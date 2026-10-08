from mlclient.xquery import cts


def run():
    return cts.field_range_query(set(), "=", "value")
