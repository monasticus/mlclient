from mlclient.xquery import cts, fn


def run():
    return cts.json_property_word_match(
        "price", "prod*", forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
