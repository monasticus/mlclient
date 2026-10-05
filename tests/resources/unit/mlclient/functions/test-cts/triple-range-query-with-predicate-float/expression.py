from mlclient.functions.xqy import cts


def run():
    return cts.triple_range_query("subject", 2.5, "object").compile()
