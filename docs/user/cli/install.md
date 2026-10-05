# install skill

Install the bundled MLClient skill for a coding agent:

```sh
ml install skill codex
ml install skill claude --dry-run
```

See [skill installation](install/skill.md) and [AI skill](../ai.md).
Successful installations record their destinations in
`~/.mlclient/ai-installations.json` so [`ml self update`](self/update.md) can refresh
them after upgrading the package. Dry runs do not create installation records.
