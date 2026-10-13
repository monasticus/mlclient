from mlclient.xquery import cts


def run():
    return cts.triples(
        subject="subject",
        predicate="predicate",
        object="object",
        operator="aln_before",
        options="checked",
        query="needle",
        forest_ids=123,
    ).compile()
