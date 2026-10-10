from mlclient.xquery import fn


def run():
    return fn.function_name(
        fn.function_lookup(
            fn.qname("http://www.w3.org/2005/xpath-functions", "count"), 1,
        ),
    ).compile()
