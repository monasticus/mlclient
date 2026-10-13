from mlclient.xquery import cts


def run():
    return cts.search(
        cts.search().pos(1),
        "needle",
        options="checked",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
