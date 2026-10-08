from mlclient.xquery import cts


def run():
    return cts.geospatial_json_property_child_reference(
        "price", "child", options="checked",
    ).compile()
