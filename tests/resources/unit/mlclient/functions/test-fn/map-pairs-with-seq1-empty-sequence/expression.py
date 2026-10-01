from mlclient.functions.xqy import cts, fn


def run():
    return fn.map_pairs(
        fn.function_lookup(
            fn.qname("http://www.w3.org/2005/xpath-functions", "count"), 1,
        ),
        None,
        cts.search().index(1),
    ).compile()
