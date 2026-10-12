# Native aggregate integration fixture

The plugin registers `mean` (double), `label` (string), `summary` (map) and
`empty` (empty sequence). All functions read the supplied range index; an empty
input produces no result. Tests use an isolated database and remove its forest
and documents afterwards. The installed plugin remains available under
`native/mlclient-test-aggregates`.

Build with GCC compatible with the local MarkLogic container and its own
`/opt/MarkLogic/include/MarkLogic.h`. Do not compile with host headers or upgrade
packages in a running MarkLogic container. On a compatible build host:

```sh
make -C tests/resources/integration/mlclient/services/native-plugin
```

For the RHEL 8 MarkLogic image, use a disposable build container. Save the SDK
headers before installing compiler dependencies: `dnf --allowerasing` can remove
the MarkLogic RPM due to its pinned glibc dependency. This is safe only in the
build container; copy the saved headers back to `/opt/MarkLogic/include` there.
Install `gcc-c++`, `make` and `zip`, then run the fixture Makefile. No MarkLogic
server needs to run in the build container.

Copy the resulting ZIP to the **local test server** and run:

```sh
docker cp tests/resources/integration/mlclient/services/native-plugin/mlclient-test-aggregates.zip mlclient_cts_query_12:/tmp/mlclient-test-aggregates.zip
MLCLIENT_CTS_PORT=18000 MLCLIENT_CTS_MANAGE_PORT=18002 \
MLCLIENT_NATIVE_PLUGIN_ZIP=/tmp/mlclient-test-aggregates.zip \
PYTHONPATH=$PWD poetry run pytest tests/integration/mlclient/services/test_native_aggregate_service.py
```

`MLCLIENT_NATIVE_PLUGIN_ZIP` is a path inside the server container, not the
client filesystem. Plugin tests skip when it is unset. An invalid package or
installation failure fails the tests. The values/built-in aggregate test always
runs. Installation uses `plugin:install-from-zip` with the test-specific plugin
ID and updates only that plugin.

MarkLogic REST JSON renders the numeric scalar as a string without its own type
annotation, despite the plugin returning `xs:double`. The service preserves that
JSON string; the direct `cts:aggregate` test verifies the native numeric type.
Maps retain the REST `map.entry` structure. REST JSON may omit entries from
multi-entry maps; the fixture uses one entry. Use raw REST XML or `cts:aggregate`
through eval when every map entry is needed.
