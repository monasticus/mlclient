# CLI reference

The installed command help is authoritative:

```sh
ml --help
ml help COMMAND
ml logs --help
```

| Command family | Operations |
| --- | --- |
| `env` | `show`, `init`, `edit`, `copy`, `compare`, `remove` |
| Evaluation | `eval` inline/file XQuery or JavaScript; `sample` bounded structure inspection |
| Requests | `http` generic requests; `url` connection URL |
| Monitoring | `health`, `version`, `logs`, `log-level`, `trace-events` |
| Updates | `self update` package upgrade and refresh installed skills; `--dry-run` previews |
| Agent setup | `install skill` |

Read [use cases](use-cases.md) for routing and the command's `--help` for exact
arguments, aliases and defaults. `http` preserves original output by default
and offers `--pretty`; `eval`/`sample` format by default and offer `--no-pretty`.
[Cluster log examples and limitations](logs.md).
