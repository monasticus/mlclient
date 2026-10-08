from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_value_match(
        "item",
        "child-names",
        "prod*",
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
