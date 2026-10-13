"""Runtime CTS queries compile but cannot be described without evaluation."""

from mlclient.xquery import cts


def run():
    return cts.parse("blue").to_json()
