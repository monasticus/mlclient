# Install and update the skill

The skill ships in the normal package. Choose an agent and project/user scope:

```sh
ml install skill codex
ml install skill claude --global
ml install skill cursor --dry-run
ml install skill copilot --force
```

| Agent | Project skill | User skill |
| --- | --- | --- |
| Codex | `.agents/skills/mlclient` | `~/.agents/skills/mlclient` |
| Claude Code | `.claude/skills/mlclient` | `~/.claude/skills/mlclient` |
| Cursor | `.cursor/skills/mlclient` | `~/.cursor/skills/mlclient` |
| Copilot | `.github/skills/mlclient` | `~/.copilot/skills/mlclient` |

Installation reports every written or unchanged file. Conflicting bundled
content needs `--force`; unrelated files remain. Restart the agent or begin a
new session. Package installation itself does not write agent files.

`ml self update` upgrades the running package from PyPI and refreshes previously
installed skills. `--dry-run` previews the plan. Recorded destinations live in
`~/.mlclient/ai-installations.json`; older installations are discovered in
supported user paths and current/ancestor projects. It does not search the
whole filesystem or install a skill that was not already present.

Use the project's invocation/virtual environment when calling CLI or Python.
Inspect installed signatures if they differ from this bundled knowledge.
