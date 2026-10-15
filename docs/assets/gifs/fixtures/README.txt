Diagnostic recording fixtures

These tapes run real ml commands. Use disposable MarkLogic development servers
with admin/admin credentials. Existing dev/docker-compose.yaml supplies the
three-node cluster and MarkLogic 10; mlclient_cts_query_12 supplies version 12.
The tapes discover current container IPs using docker inspect.

For logs and trace-events, create a REST instance named vhs-bookstore on port
8010, using the existing Documents database. Seed actual alternating-node logs
with the mlclient-dev skill's seed-terminal-logs.py. Send three GET requests to
/v1/ping on node 1 to produce access log entries.

Before trace-events, save the group's activation flag and enabled events. Enable
CPF Actions, Optic Query Execution and SQL Query Execution and activate tracing.
The tape adds two further events, then removes CPF Actions and Optic Query
Execution in the interactive selector and activates tracing again.

Before log-level, save the Default group's file/system levels and the demo
App Server's file level. The tape sets all twelve group file log levels.

For health, copy the three .xqy files here into a fresh directory inside node 1.
Create a disposable HTTP App Server named vhs-health on port 8011, with that
root directory, filesystem modules, Documents content database,
application-level authentication, default-user admin and /rewrite.xqy as its
URL rewriter. This isolated demo endpoint returns HTTP 503 for its first eight
health requests, then HTTP 200. It demonstrates polling and recovery without
changing the built-in HealthCheck service or stopping other applications.
Use a fresh App Server for each health recording to reset the probe counter.

GET /orders.xqy once on port 8011 after the health recording. It creates a real,
compact request log entry with xdmp:request-log-put. The logs tape reads it from
8011_RequestLog.txt; the other log scenes read the bookstore REST server on 8010.

After recording, restore the saved trace configuration and log levels. Delete
the vhs-health App Server and its temporary filesystem directory. Delete only
the vhs-bookstore REST instance and its modules database (include=modules),
never the shared Documents database. Restore the original container state.
