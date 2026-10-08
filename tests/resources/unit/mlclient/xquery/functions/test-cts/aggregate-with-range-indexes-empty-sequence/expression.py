from mlclient.xquery import cts


def run():
    return cts.aggregate("/ext/aggregate.so", "total", None).compile()
