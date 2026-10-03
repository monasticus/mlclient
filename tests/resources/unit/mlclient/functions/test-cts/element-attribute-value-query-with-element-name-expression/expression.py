from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_value_query(
        fn.qname("https://example.com/products", "p:item"), "id", "MarkLogic search",
    ).compile()
