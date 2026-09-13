# Read server logs

`ml.logs` returns parsed log records through the Management API. Use the
[logs command](../cli/logs.md) when you only need terminal output.

```python
from mlclient import MLClient

with MLClient() as ml:
    for record in ml.logs.get(8002, "error"):
        print(record)
```

The Management connection uses its own configuration, normally port 8002.
Filtering by time and log type is documented in the
[service reference][mlclient.services.LogsService]. Use a time range for large
logs rather than retrieving a whole file repeatedly.

Server-side log levels are a separate operation: see
[log-level configuration](operations.md#log-level-configuration).
