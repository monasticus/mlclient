from mlclient.xquery import cts


def run():
    return cts.element_attribute_value_query(set(), "id", "MarkLogic search")
