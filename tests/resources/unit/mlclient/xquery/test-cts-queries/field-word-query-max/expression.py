"""Native field word query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.field_word_query("title", "blue", options="lang=en", weight=2)
