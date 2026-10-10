from mlclient.xquery import cts, fn


def run():
    return cts.document_permission_query(
        "reader", fn.string(cts.search().pos(1)),
    ).compile()
