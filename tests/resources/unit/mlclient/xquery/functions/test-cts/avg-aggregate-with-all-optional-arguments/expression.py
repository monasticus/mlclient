from mlclient.xquery import cts


def run():
    return cts.avg_aggregate(
        cts.element_reference("price"),
        options="checked",
        query="needle",
        forest_ids=123,
    ).compile()
