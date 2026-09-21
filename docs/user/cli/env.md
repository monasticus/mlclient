# env

An MLClient environment is a YAML file containing the connection settings for a
project. The `env` command group creates and inspects those files; it does not
create databases or deploy a MarkLogic application.

| Command | Use it to |
| --- | --- |
| [`ml env init`](env/init.md) | Create a template, import ml-gradle properties or discover App Servers from a host |
| [`ml env show`](env/show.md) | List environments, inspect a configuration or copy a simple setting |
| [`ml env edit`](env/edit.md) | Open a configuration file in your editor |
| [`ml env copy`](env/copy.md) | Clone a configuration under a new name, optionally editing it |

## Create and inspect a configuration

```sh
ml env init
ml env show local
```

Review `.mlclient/mlclient-local.yaml` and fill in your connection settings
before sending requests. Other commands use `local` by default; `-e dev` selects
`.mlclient/mlclient-dev.yaml` instead.

An environment can name several connections. For the file format, inherited
settings and use from Python, see [Environments](../environments.md).
