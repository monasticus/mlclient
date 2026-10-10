from mlclient.xquery import cts, fn


def run():
    return fn.fold_left(
        fn.function_lookup(
            fn.qname("http://www.w3.org/2005/xpath-functions", "count"), 1,
        ),
        None,
        cts.search().pos(1),
    ).compile()
