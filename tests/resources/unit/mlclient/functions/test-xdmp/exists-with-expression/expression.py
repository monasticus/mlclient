from mlclient.functions.xqy import cts, xdmp


def run():
    return xdmp.exists(cts.search(query=cts.true_query()).pos(1)).compile()
