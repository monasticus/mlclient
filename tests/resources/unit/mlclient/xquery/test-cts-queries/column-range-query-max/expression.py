"""Public compilation and native serialization of ColumnRangeQuery."""

from mlclient.xquery import cts


def run():
    original = cts.column_range_query(
        "reports",
        "items",
        "price",
        2,
        operator=">=",
        options="cached",
        weight=2,
    )
    return original.with_column_id(11548423394257569743)
