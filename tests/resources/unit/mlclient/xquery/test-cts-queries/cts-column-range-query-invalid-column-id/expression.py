"""Public compilation and native serialization of ColumnRangeQuery."""

from mlclient.xquery import cts


def run():
    query = cts.column_range_query("reports", "items", "price", 2)
    return query.with_column_id(-1)
