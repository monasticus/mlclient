from mlclient.xquery import cts


def run():
    return cts.field_value_query(None, "MarkLogic search").compile()
