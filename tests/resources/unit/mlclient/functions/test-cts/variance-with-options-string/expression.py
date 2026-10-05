from mlclient.functions.xqy import cts


def run():
    return cts.variance(cts.element_reference("price"), options="checked").compile()
