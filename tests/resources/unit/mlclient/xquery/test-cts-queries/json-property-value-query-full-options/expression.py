from mlclient.xquery import cts


def run():
    return cts.json_property_value_query("label", "gamma", options="exact", weight=3)
