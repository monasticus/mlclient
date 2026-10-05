# AI skill

MLClient includes a skill that teaches a coding agent to use the CLI and Python
API and to write appropriate MarkLogic queries. No extra dependencies are needed.
Installing the package alone does not change agent configuration.

```sh
ml install skill codex
ml install skill claude
ml install skill cursor
ml install skill copilot
```

Use `--global` for personal installation, `--dry-run` to inspect paths, and
`--force` to refresh bundled files. Start a new session or restart the agent.

The skill maps tasks to CLI commands, Python services, named API wrappers and
raw HTTP when necessary. It covers async concurrency and cancellation, retry
and timeout configuration, documents/metadata, transactions, cluster logs,
ml-gradle projects, index discovery, XQuery correctness and query planning.

Additional references cover URI cursor/export flows, Python XQuery builders,
Optic/TDE, RDF/SPARQL, temporal data, permissions, modules and server-side tests.
Python examples use library builders or evaluate separate source files with
external variables. The skill includes complete exported REST contracts for
MarkLogic 10–12 and practical templates, loaded only when relevant. Exact Python
signatures are inspected in the installed library rather than duplicated.

`ml self update` upgrades the package from PyPI and refreshes installed skills.
Use `ml self update --dry-run` to inspect the plan. See
[self-update](cli/self/update.md) for installation discovery and failure handling.
