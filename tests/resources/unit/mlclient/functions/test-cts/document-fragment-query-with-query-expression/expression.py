from mlclient.functions.xqy import cts


def run():
    return cts.document_fragment_query(cts.collection_query("products")).compile()
