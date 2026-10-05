from mlclient.functions.xqy import cts


def run():
    return cts.aggregate("/ext/aggregate.so", "total", None).compile()
