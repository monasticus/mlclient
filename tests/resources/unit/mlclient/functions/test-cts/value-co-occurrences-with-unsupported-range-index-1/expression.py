from mlclient.functions.xqy import cts


def run():
    return cts.value_co_occurrences(set(), cts.element_reference("price"))
