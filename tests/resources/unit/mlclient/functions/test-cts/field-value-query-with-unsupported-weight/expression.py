from mlclient.functions.xqy import cts


def run():
    return cts.field_value_query("description", "MarkLogic search", weight=set())
