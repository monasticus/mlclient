"""Native json property scope query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.json_property_scope_query(["report", "note"], cts.true_query())
