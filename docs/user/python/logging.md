# Logging to MarkLogic

[`MLLogHandler`][mlclient.logging.MLLogHandler] is a standard
`logging.Handler` that forwards the records it receives to a
MarkLogic server's error log through `xdmp:log`. Attach it next to your console
or file handlers and the same message lands in both places - MarkLogic prepends
its own timestamp and renders the level, so the forwarded line carries only the
logger name and the message.

Forwarding is non-blocking: a record is queued and a single background thread
sends it, so logging never waits on the network.

## Which loggers are forwarded

This is ordinary logging configuration, not a handler setting. A handler
receives the records of the loggers it is attached to (and their children), so
you choose the scope the same way you would wire an appender in Spring:

- attach it to the **root logger** to forward everything, including third-party
  libraries such as `httpx`;
- attach it to **your application logger** (`my_app`) to forward only your own
  records;
- attach it to a **named third-party logger** (`httpx`, `urllib3`) to add just
  that library.

The handler drops the records its own MarkLogic client emits while sending, so
attaching it to the root logger does not create a feedback loop.

## Connecting to MarkLogic

Configure one of two mutually exclusive connection modes:

| Setting | Mode | Meaning |
|---|---|---|
| `environment` (+ optional `app_server`) | named environment | Load a `.mlclient` environment; `app_server` picks a REST server, otherwise the first one. |
| `host`, `port`, `protocol`, `username`, `password`, `auth` | connection details | Build a client directly. |
| `ssl` (`verify`, `cert_file`, `key_file`, `key_password`) | connection details | Enable TLS; any value forces HTTPS. |

Passing an `environment` together with any connection detail raises
`WrongParametersError`.

The forwarded message should omit the date and the level: give the handler a
formatter such as `"%(name)s - %(message)s"`, since MarkLogic adds the timestamp
and level itself.

## Recipe 1: configure everything in YAML

Point the handler at an environment (or connection details) directly in a
`logging.config.dictConfig` document:

```yaml
version: 1
formatters:
  console:
    format: "%(asctime)s %(levelname)s %(name)s - %(message)s"
  marklogic:
    format: "%(name)s - %(message)s"
handlers:
  console:
    class: logging.StreamHandler
    formatter: console
  marklogic:
    class: mlclient.logging.MLLogHandler
    formatter: marklogic
    environment: local
loggers:
  my_app:
    level: INFO
    handlers: [console, marklogic]
```

```python
import logging.config

import yaml

with open("logging.yaml") as config_file:
    logging.config.dictConfig(yaml.safe_load(config_file))

logging.getLogger("my_app").info("deploy finished")
```

## Recipe 2: YAML config, environment from code

Keep the handler declarative but supply the environment (and optionally the app
server) at runtime with
[`setup_ml_logger`][mlclient.logging.setup_ml_logger]. Omit `environment` from
the `marklogic` handler in the YAML above, then:

```python
from mlclient.logging import setup_ml_logger

setup_ml_logger("logging.yaml", environment="local", app_server="content")

import logging

logging.getLogger("my_app").info("deploy finished")
```

`setup_ml_logger` injects `environment` and `app_server` into the handler whose
id is `handler_id` (default `marklogic`) only when you pass them, then applies
the configuration.

## Recipe 3: configure in Python

Without YAML you wire the formatters and handlers yourself:

```python
--8<-- "examples/ml_logging.py"
```

```python
from ml_logging import build_logger

logger = build_logger()
logger.info("deploy finished")
```

!!! note "The FINE level"

    Importing `mlclient` registers a custom `FINE` level (one below `DEBUG`) and
    a `logger.fine(...)` method. You can log with it (`logger.fine("...")`) and
    forward it like any other level. If your application already defines its own
    `FINE` level or `fine` method, be aware of the clash.

## See also

- [Evaluate code](eval.md) - the `xdmp:log` call runs through `ml.eval`.
- [`MLLogHandler`][mlclient.logging.MLLogHandler] - the full reference.
