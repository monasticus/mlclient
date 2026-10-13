from mlclient.xquery import cts


def run():
    return cts.field_value_co_occurrences("field-name-1", "field-name-2", query=set())
