# self update

Upgrade the running MLClient installation from PyPI, then refresh previously
installed agent skills using the upgraded package.

```sh
ml self update --dry-run
ml self update
```

The command uses pipx or uv for their managed tool environments, and pip in the
running Python environment otherwise. An environment without pip can use uv.
Managed tools retain their installation settings, including version constraints.

`install skill` records successful installation destinations
in `~/.mlclient/ai-installations.json`. Self-update checks those destinations,
including other projects. For installations made before tracking was added,
it also checks the current project, its ancestors and supported user locations.
It skips removed skills and does not search every directory on disk.

The plan lists the package-manager command and integration destinations.
`--dry-run` runs no processes and writes no files. Refresh installers report
individual file changes. Skill refresh replaces bundled files; keep local additions in separate files.

A package upgrade failure leaves agent files untouched. A later integration
failure reports a partial update and returns a nonzero status; correct the
reported issue and rerun the command. Restart the agent or start a new session
after completion. The command does not edit project dependency/lock files.

Package-manager references: [pipx upgrades](https://pipx.pypa.io/stable/reference/cli/#pipx-upgrade)
and [uv tool upgrades](https://docs.astral.sh/uv/concepts/tools/#upgrading-tools).

## Options

### `--dry-run`

Show the package upgrade command and skills to refresh without running
processes or writing files.
