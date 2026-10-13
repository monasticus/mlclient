from mlclient.xquery import cts


def run():
    return cts.distinctive_terms(cts.search().pos(1), options=set())
