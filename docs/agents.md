# AI agents

MLClient provides two execution interfaces: the Python library and the `ml` CLI.
An AI agent can use either through the tools available in its host application.
A skill supplies usage guidance; an MCP server exposes selected operations as
tools. Both are adapters around those interfaces.

## Using the current package

Give the agent the same project environment you would use yourself, and start
with ordinary commands:

```sh
ml --help
ml env show
ml version
```

The [CLI guide](user/cli.md) explains connection selection. For a repeatable
workflow, a small Python script using the [Python guide](user/pythonapi.md) can
be easier to test than a sequence of generated commands.

Use credentials appropriate to the task. Keep passwords and tokens out of
prompts, committed files and captured output. Treat writes, eval and administrative
operations according to the approval rules of the agent's host; a natural-language
request is not a reason to grant an account broader server privileges.

## MCP and skills

This package currently ships neither an MCP server nor an installable end-user
skill. Dedicated distribution and setup instructions will be added when those
adapters are available. The development guidance used to maintain MLClient is
not an end-user integration bundled by `pip install mlclient`.

An adapter should preserve the library's connection configuration, error details
and timeout behavior, and expose only the operations needed for its use case.
There is no separate configuration format to learn just to use the current CLI
from an agent.
