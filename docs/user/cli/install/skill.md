# install skill

Copy MLClient's skill, references and templates into a coding agent's skill
directory. This works with the standard package, without optional extras.

```sh
ml install skill codex
ml install skill claude --global
ml install skill cursor --dry-run
ml install skill copilot --force
```

The command reports each written or unchanged file. It checks all destinations
before writing, rejects symlinks, and retains unrelated files. Reinstalling an
identical skill does not rewrite it. After upgrading MLClient, use `--force`
to replace the previous bundled files. Start a new agent session afterwards.

## Arguments

### `agent`

Optional. One of `codex`, `claude`, `cursor`, `copilot`. Omit to choose
interactively; noninteractive use requires a value. `claude` means Claude Code,
`copilot` means VS Code at project scope and Copilot's user skill directory globally.

## Options

### `--global`, `-g`

Install into your home directory rather than the current project's directory.
See [AI integration](../../ai.md) for each destination.

### `--force`, `-f`

Replace changed MLClient files. Unrelated skill directories and extra user files
inside the destination are retained. The skill should be customized in the
project's own instructions rather than edited in place if updates must preserve it.

### `--dry-run`

Print the proposed file paths without creating directories or writing files.
Conflict checks still apply; combine with `--force` to preview an update.
