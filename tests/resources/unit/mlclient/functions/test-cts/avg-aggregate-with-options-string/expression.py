from mlclient.functions.xqy import cts


def run():
    return cts.avg_aggregate(
        cts.element_reference("price"), options="checked",
    ).compile()
