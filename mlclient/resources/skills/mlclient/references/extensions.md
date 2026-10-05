# Custom application APIs

Use `.http` for a one-off custom route. Add a named Call/wrapper only when a
project repeats the operation and benefits from validation or a stable method.
Add a service only for parsing, orchestration or lifecycle behavior.

Copy [custom_api.py](../assets/custom_api.py), which demonstrates both sync and
async using public imports. It gives `MyAppMLClient.rest.my_awesome_endpoint()`
and `await AsyncMyAppMLClient.rest.my_awesome_endpoint()` for a hypothetical
`GET /app/tasks` route. Replace the route and response contract with the
application's actual deployed endpoint; MLClient does not install that route.

1. Subclass `ApiCall`. Describe method, endpoint, headers, parameters and body.
   Calls perform no I/O. Reuse the same Call for sync and async wrappers.
2. Build a RestApi/AsyncRestApi subclass using its public `.call(...)` method.
   Return `httpx.Response` from the API method and forward keyword-only timeout.
3. Override `.rest` with a cached property on an MLClient/AsyncMLClient subclass,
   constructed with `ApiClient(self.http)` / `AsyncApiClient(self.http)`. Keep the
   parent's ownership of authentication, pooling and cleanup.
4. If a parsed result adds value, define a separate service using the public API
   method, check status and parse. Avoid private library state or duplicate HTTP
   sessions. Keep exceptions and async methods explicit.
5. Test against the wire (method/path/query/body/headers/timeouts) plus parsed
   success and native server error behavior. Use representative recorded server
   fixtures where available; clearly label hypothetical app payloads.

`ApiCall.add_param` currently drops falsey values. If an endpoint requires `0`,
`false` or an empty string, verify the final request or use raw HTTP for that
contract; do not assume constructor kwargs preserve every value. Escape dynamic
resource names as individual path segments. Body dict encoding depends on
Content-Type; provide the endpoint's explicit MIME type.

Documentation: [custom APIs](https://monasticus.github.io/mlclient/user/python/custom-api/),
[API methods](api-methods.md), [public imports](python-cli.md).
