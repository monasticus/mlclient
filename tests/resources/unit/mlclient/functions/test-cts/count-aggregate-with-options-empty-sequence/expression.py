from mlclient.functions.xqy import cts


def run():
    return cts.count_aggregate(cts.element_reference("price"), options=None).compile()
