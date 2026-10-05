from mlclient.functions.xqy import cts


def run():
    return cts.estimate(
        "needle", options="checked", quality_weight=2.5, forest_ids=123, maximum=2.5,
    ).compile()
