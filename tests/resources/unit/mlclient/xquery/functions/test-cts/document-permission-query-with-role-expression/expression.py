from mlclient.xquery import cts, fn


def run():
    return cts.document_permission_query(
        fn.string(cts.search().pos(1)), "read",
    ).compile()
