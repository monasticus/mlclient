from mlclient.xquery import cts


def run():
    return cts.field_value_match(
        "field-names", "prod*", query=cts.collection_query("products"),
    ).compile()
