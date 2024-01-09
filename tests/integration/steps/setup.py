from __future__ import annotations

from time import sleep

from pytest_bdd import given, parsers

from mlclient import MLResourcesClient


@given(
    parsers.parse("I produce {count} test logs\n{pattern}"),
    target_fixture="test_logs_count",
)
def produce_logs(
    count: str,
    pattern: str,
    client: MLResourcesClient,
) -> int:
    count = int(count)
    for i in range(1, count + 1):
        log = pattern.replace("<i>", str(i))
        client.eval(xquery=f'xdmp:log("{log}", "error")')
    return count


@given(
    parsers.parse("I wait {seconds} second(s)"),
)
def wait(
    seconds: str,
):
    sleep(int(seconds))
