"""Native directory query serialization and compilation."""

from mlclient.xquery import DirectoryQuery, xs


def run():
    return DirectoryQuery("/reports/", xs.string("2")).serialize()
