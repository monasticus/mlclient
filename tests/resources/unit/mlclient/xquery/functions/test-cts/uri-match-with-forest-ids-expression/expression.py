from mlclient.xquery import cts, fn


def run():
    return cts.uri_match("prod*", forest_ids=fn.count(cts.search().pos(1))).compile()
