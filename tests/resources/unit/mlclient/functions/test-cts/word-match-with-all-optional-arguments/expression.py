from mlclient.functions.xqy import cts


def run():
    return cts.word_match(
        "prod*", options="checked", query="needle", quality_weight=2.5, forest_ids=123,
    ).compile()
