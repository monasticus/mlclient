from mlclient.xquery import cts


def run():
    return cts.json_property_word_query(
        "price", "MarkLogic search", options=["checked"],
    ).compile()
