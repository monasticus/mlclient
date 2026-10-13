from mlclient.xquery import cts


def run():
    return cts.triples(subject="subject").compile()
