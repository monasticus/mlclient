from mlclient.xquery import cts


def run():
    return cts.field_values(
        "field-names", query=cts.collection_query("products"),
    ).compile()
