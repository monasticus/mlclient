from mlclient.xquery import cts


def run():
    return cts.values(cts.element_reference("price"), quality_weight=set())
