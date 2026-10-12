"""Native json property word query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.json_property_word_query(
        ["title", "body"],
        ["blue", "green"],
        options=["lang=en", "exact"],
        weight=2,
    )
