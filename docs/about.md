# Background and direction

MLClient is an independent Python library and CLI for MarkLogic. It offers
synchronous and asynchronous clients, document models and services, REST/Manage/
Admin wrappers, and direct HTTP access. Its client layers compose HTTPX transport
rather than subclassing a third-party HTTP session API.

## Why another client?

I began MLClient roughly eight months before the
[MarkLogic Python Client](https://github.com/marklogic/marklogic-python-client)
project began, and developed it without knowing that client had appeared. After
putting my project aside for a few years, I returned to it and discovered the
other library. I chose to continue because I enjoy Python and wanted to build on
the work already started.

The purpose is to offer another useful choice. If a requests-based client covers
your needs and you do not need MLClient's async interfaces or CLI, the MarkLogic
Python Client is worth considering. Its own documentation describes its supported
operations and authentication; this is not a claim that the two libraries have
identical scope or that every feature differs.

MLClient focuses on async alongside sync, explicit connection/authentication
configuration, several API levels, custom application extensions, and a CLI that
can use multiple configured connections. The guides show those capabilities with
working examples rather than requiring every application to use every layer.

## What comes next

Broader REST endpoint coverage is a direction, not a claim of completeness today.
The CLI may also grow project-management workflows as another option alongside
tools such as [ml-gradle](https://github.com/marklogic/ml-gradle). It does not
currently replace ml-gradle's deployment functionality.

Agent integrations are another way to use the library and CLI, not a separate
database API. See [AI agents](agents.md) for the current boundary. More useful
tools and approaches can make MarkLogic easier to adopt; users should be able
to choose the workflow that fits their application.
