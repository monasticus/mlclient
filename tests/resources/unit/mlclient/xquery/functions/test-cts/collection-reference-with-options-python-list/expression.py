from mlclient.xquery import cts


def run():
    return cts.collection_reference(options=["checked"]).compile()
