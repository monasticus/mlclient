from mlclient.functions.xqy import cts


def run():
    return cts.value_co_occurrences(
        cts.element_reference("price"),
        cts.element_reference("price"),
        quality_weight=None,
    ).compile()
