from mlclient.xquery import cts


def run():
    return cts.triples(object=123).compile()
