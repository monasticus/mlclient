from mlclient.functions.xqy import cts


def run():
    return cts.covariance_p(
        cts.element_reference("price"),
        cts.element_reference("price"),
        options="checked",
    ).compile()
