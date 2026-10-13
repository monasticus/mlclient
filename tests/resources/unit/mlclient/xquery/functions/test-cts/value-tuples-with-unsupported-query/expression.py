from mlclient.xquery import cts


def run():
    return cts.value_tuples(cts.element_reference("price"), query=set())
