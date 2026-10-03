from mlclient.functions.xqy import cts


def run():
    return cts.element_geospatial_value_match(
        "item", "prod*", options="checked",
    ).compile()
