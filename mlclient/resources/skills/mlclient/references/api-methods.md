# Named API methods

Use the same methods with `await` on AsyncMLClient. Parameters below are actual Python signatures; `timeout` controls transport, not endpoint query data.

## `ml.manage.databases.delete`

`DELETE /manage/v2/databases/[id-or-name]`

```python
self, database: str, *, forest_delete: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/DELETE/manage/v2/databases/%5Bid-or-name%5D)

## `ml.manage.forests.delete`

`DELETE /manage/v2/forests/[id-or-name]`

```python
self, forest: str, *, level: str, replicas: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/DELETE/manage/v2/forests/%5Bid-or-name%5D)

## `ml.manage.roles.delete`

`DELETE /manage/v2/roles/[id-or-name]`

```python
self, role: str, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/DELETE/manage/v2/roles/%5Bid-or-name%5D)

## `ml.manage.servers.delete`

`DELETE /manage/v2/servers/[id-or-name]`

```python
self, server: str, group_id: str, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/DELETE/manage/v2/servers/%5Bid-or-name%5D)

## `ml.manage.users.delete`

`DELETE /manage/v2/users/[id-or-name]`

```python
self, user: str, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/DELETE/manage/v2/users/%5Bid-or-name%5D)

## `ml.rest.documents.delete`

`DELETE /v1/documents`

```python
self, uri: str | list, *, database: str | None=None, category: str | list | None=None, txid: str | None=None, temporal_collection: str | None=None, system_time: str | None=None, wipe_temporal: bool | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/DELETE/v1/documents)

## `ml.admin.get_server_config`

`GET /admin/v1/server-config`

```python
self, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/admin/v1/server-config)

## `ml.admin.get_timestamp`

`GET /admin/v1/timestamp`

```python
self, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/admin/v1/timestamp)

## `ml.manage.databases.get_list`

`GET /manage/v2/databases`

```python
self, *, data_format: str | None=None, view: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/databases)

## `ml.manage.databases.get`

`GET /manage/v2/databases/[id-or-name]`

```python
self, database: str, *, data_format: str | None=None, view: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/databases/%5Bid-or-name%5D)

## `ml.manage.databases.get_properties`

`GET /manage/v2/databases/[id-or-name]/properties`

```python
self, database: str, *, data_format: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/databases/%5Bid-or-name%5D/properties)

## `ml.manage.forests.get_list`

`GET /manage/v2/forests`

```python
self, *, data_format: str | None=None, view: str | None=None, database: str | None=None, group: str | None=None, host: str | None=None, full_refs: bool | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/forests)

## `ml.manage.forests.get`

`GET /manage/v2/forests/[id-or-name]`

```python
self, forest: str, *, data_format: str | None=None, view: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/forests/%5Bid-or-name%5D)

## `ml.manage.forests.get_properties`

`GET /manage/v2/forests/[id-or-name]/properties`

```python
self, forest: str, *, data_format: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/forests/%5Bid-or-name%5D/properties)

## `ml.manage.groups.get_properties`

`GET /manage/v2/groups/[id-or-name]/properties`

```python
self, group: str, *, data_format: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/groups/%5Bid-or-name%5D/properties)

## `ml.manage.hosts.get_list`

`GET /manage/v2/hosts`

```python
self, *, data_format: str | None=None, group_id: str | None=None, view: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/hosts)

## `ml.manage.logs.get`

`GET /manage/v2/logs`

```python
self, filename: str, *, data_format: str | None=None, host: str | None=None, start_time: str | None=None, end_time: str | None=None, regex: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/logs)

## `ml.manage.roles.get_list`

`GET /manage/v2/roles`

```python
self, *, data_format: str | None=None, view: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/roles)

## `ml.manage.roles.get`

`GET /manage/v2/roles/[id-or-name]`

```python
self, role: str, *, data_format: str | None=None, view: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/roles/%5Bid-or-name%5D)

## `ml.manage.roles.get_properties`

`GET /manage/v2/roles/[id-or-name]/properties`

```python
self, role: str, *, data_format: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/roles/%5Bid-or-name%5D/properties)

## `ml.manage.servers.get_list`

`GET /manage/v2/servers`

```python
self, *, data_format: str | None=None, group_id: str | None=None, view: str | None=None, full_refs: bool | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/servers)

## `ml.manage.servers.get`

`GET /manage/v2/servers/[id-or-name]`

```python
self, server: str, group_id: str, *, data_format: str | None=None, view: str | None=None, host_id: str | None=None, full_refs: bool | None=None, modules: bool | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/servers/%5Bid-or-name%5D)

## `ml.manage.servers.get_properties`

`GET /manage/v2/servers/[id-or-name]/properties`

```python
self, server: str, group_id: str, *, data_format: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/servers/%5Bid-or-name%5D/properties)

## `ml.manage.users.get_list`

`GET /manage/v2/users`

```python
self, *, data_format: str | None=None, view: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/users)

## `ml.manage.users.get`

`GET /manage/v2/users/[id-or-name]`

```python
self, user: str, *, data_format: str | None=None, view: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/users/%5Bid-or-name%5D)

## `ml.manage.users.get_properties`

`GET /manage/v2/users/[id-or-name]/properties`

```python
self, user: str, *, data_format: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/manage/v2/users/%5Bid-or-name%5D/properties)

## `ml.rest.documents.get`

`GET /v1/documents`

```python
self, uri: str | list, *, database: str | None=None, category: str | list | None=None, data_format: str | None=None, timestamp: str | None=None, transform: str | None=None, transform_params: dict | None=None, txid: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/v1/documents)

## `ml.rest.transactions.get`

`GET /v1/transactions/[txid]`

```python
self, txid: str, *, data_format: str | None=None, database: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/GET/v1/transactions/%5Btxid%5D)

## `ml.manage.databases.create`

`POST /manage/v2/databases`

```python
self, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/manage/v2/databases)

## `ml.manage.databases.post`

`POST /manage/v2/databases/[id-or-name]`

```python
self, database: str, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/manage/v2/databases/%5Bid-or-name%5D)

## `ml.manage.forests.create`

`POST /manage/v2/forests`

```python
self, body: str | dict, *, wait_for_forest_to_mount: bool | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/manage/v2/forests)

## `ml.manage.forests.post`

`POST /manage/v2/forests/[id-or-name]`

```python
self, forest: str, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/manage/v2/forests/%5Bid-or-name%5D)

## `ml.manage.roles.create`

`POST /manage/v2/roles`

```python
self, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/manage/v2/roles)

## `ml.manage.servers.create`

`POST /manage/v2/servers`

```python
self, body: str | dict, *, group_id: str | None=None, server_type: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/manage/v2/servers)

## `ml.manage.users.create`

`POST /manage/v2/users`

```python
self, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/manage/v2/users)

## `ml.rest.documents.post`

`POST /v1/documents`

```python
self, body_parts: list[DocumentsBodyPart], *, database: str | None=None, transform: str | None=None, transform_params: dict | None=None, txid: str | None=None, temporal_collection: str | None=None, system_time: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/v1/documents)

## `ml.rest.eval.post`

`POST /v1/eval`

```python
self, *, xquery: str | None=None, javascript: str | None=None, variables: dict | None=None, database: str | None=None, txid: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/v1/eval)

## `ml.rest.transactions.create`

`POST /v1/transactions`

```python
self, *, name: str | None=None, time_limit: int | None=None, database: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/v1/transactions)

## `ml.rest.transactions.post`

`POST /v1/transactions/[txid]`

```python
self, txid: str, *, result: str, database: str | None=None, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/POST/v1/transactions/%5Btxid%5D)

## `ml.manage.databases.put_properties`

`PUT /manage/v2/databases/[id-or-name]/properties`

```python
self, database: str, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/PUT/manage/v2/databases/%5Bid-or-name%5D/properties)

## `ml.manage.forests.put`

`PUT /manage/v2/forests`

```python
self, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/PUT/manage/v2/forests)

## `ml.manage.forests.put_properties`

`PUT /manage/v2/forests/[id-or-name]/properties`

```python
self, forest: str, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/PUT/manage/v2/forests/%5Bid-or-name%5D/properties)

## `ml.manage.groups.put_properties`

`PUT /manage/v2/groups/[id-or-name]/properties`

```python
self, group: str, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/PUT/manage/v2/groups/%5Bid-or-name%5D/properties)

## `ml.manage.roles.put_properties`

`PUT /manage/v2/roles/[id-or-name]/properties`

```python
self, role: str, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/PUT/manage/v2/roles/%5Bid-or-name%5D/properties)

## `ml.manage.servers.put_properties`

`PUT /manage/v2/servers/[id-or-name]/properties`

```python
self, server: str, group_id: str, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/PUT/manage/v2/servers/%5Bid-or-name%5D/properties)

## `ml.manage.users.put_properties`

`PUT /manage/v2/users/[id-or-name]/properties`

```python
self, user: str, body: str | dict, *, timeout=UNSET
```

[MarkLogic 12 contract](https://docs.marklogic.com/12.0/REST/PUT/manage/v2/users/%5Bid-or-name%5D/properties)
