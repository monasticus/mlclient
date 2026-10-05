from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", child_2_name_2="child-2-name-2",
    ).compile()
