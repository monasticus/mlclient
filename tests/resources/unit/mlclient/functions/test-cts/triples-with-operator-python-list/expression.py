from mlclient.functions.xqy import cts


def run():
    return cts.triples(operator=["aln_before"]).compile()
