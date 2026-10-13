from mlclient.xquery import cts


def run():
    return cts.element_value_query("title", text="*", options="exact", weight=3)
