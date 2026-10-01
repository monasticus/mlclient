from mlclient.functions.xqy import cts


def run():
    return cts.element_child_geospatial_values(
        "item",
        "child-names",
        start=cts.search().index(1),
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
