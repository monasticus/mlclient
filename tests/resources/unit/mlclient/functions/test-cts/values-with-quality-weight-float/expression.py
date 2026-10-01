from mlclient.functions.xqy import cts


def run():
    return cts.values(cts.element_reference("price"), quality_weight=2.5).compile()
