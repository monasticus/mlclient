"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import cts, fn


def run():
    query = cts.and_query(
        [cts.word_query("blue"), cts.not_query(cts.word_query(fn.string("x")))],
    )
    return query.to_xml()
