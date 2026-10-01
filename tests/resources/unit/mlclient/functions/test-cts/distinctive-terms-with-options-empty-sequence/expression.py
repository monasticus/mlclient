from mlclient.functions.xqy import cts


def run():
    return cts.distinctive_terms(cts.search().index(1), options=None).compile()
