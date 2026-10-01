from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", child_1_name_1=fn.string(cts.search().index(1)),
    ).compile()
