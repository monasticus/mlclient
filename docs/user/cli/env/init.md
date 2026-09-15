# env init

Create a project environment from a template, ml-gradle properties or a running
MarkLogic host.

```sh
ml env init
```

With no name, a wizard asks for the environment name and configuration source.
To write a commented template directly:

```sh
ml env init local
```

Import a Gradle profile or discover App Servers from a host:

```sh
ml env init --from-gradle=dev
ml env init local --from-host=localhost:8002 --interactive
```

The result is `.mlclient/mlclient-<name>.yaml` in the current directory. Review
it with [`ml env show`](show.md) before making requests. See
[Environments](../../environments.md) for the file format and Python usage.

## Arguments

### `name`

Optional environment name. With a name and no source option, write a fully
commented template. Omit the name to run the wizard. A named Gradle profile can
supply the name automatically; see `--from-gradle` below.

## Options

### `--interactive`, `-i`

Run the wizard even when a name is supplied. Host discovery asks only for fields
not already provided through options; the password prompt does not echo input.

### `--from-gradle`

Read ml-gradle properties. Accepts an environment name or a `.properties` file
path. Cannot be combined with `--from-host`.

A profile name merges `gradle-<name>.properties` over `gradle.properties` and also
names the MLClient environment:

```sh
ml env init --from-gradle=dev
ml env init my-dev --from-gradle=dev
```

A file path is read on its own, without an overlay merge. Supply a name or the
command prompts for one:

```sh
ml env init dev --from-gradle=./gradle-dev.properties
```

Passing `--from-gradle` without a value prompts for the name and selector.
An unknown profile or missing file is reported before prompting, with available
profiles or files to help identify the correct source.

### `--from-host`

Discover App Servers through a host's Manage API. Accepts `host`, `host:port`
or `protocol://host[:port]`.

```sh
ml env init dev --from-host=ml.example.com:8002 --interactive
```

When both a name and this option are supplied, discovery is non-interactive
unless `--interactive` is passed. Unspecified values default to HTTP,
`localhost`, port `8002`, username/password `admin`/`admin`, and Digest auth.
An option without a value uses these defaults; omitting the name starts prompts.

For HTTPS discovery, certificate verification is disabled and the generated YAML
contains `ssl: {verify: false}`. Set `ssl.verify` to a trusted CA bundle in the
result when verification is required.

The target URL is printed before discovery. The generated file omits unchanged
predefined servers and includes a comment listing their defaults.

### `--app-name`

Application label. For host discovery, also restricts results to matching
App Server names. Without it, all discovered servers are retained and the label
is left commented out.

```sh
ml env init dev --from-host=ml.example.com --app-name=my-app --interactive
```

### `--username`, `-u`

Username for host discovery. Defaults to `admin` in non-interactive mode.

### `--password`, `-p`

Password for host discovery. Defaults to `admin` in non-interactive mode.
An explicit empty value (`--password=''`) is preserved. At an interactive prompt,
Enter accepts the displayed default.

### `--auth`, `-a`

Host-discovery authentication: `basic`, `digest` (default) or `digestbasic`.
Other values are rejected.

### `--global`, `-g`

Write to `.mlclient` in your home directory instead of the current directory.

### `--force`, `-f`

Overwrite an existing environment file. Without this flag, an existing file is
left untouched and the command reports an error.

See also [global options](../../cli.md#global-options).

## Discovery and connection settings

For `localhost` and IP addresses, each server's own protocol and authentication
are recorded when they differ from the root configuration. Other hostnames are
treated as load-balanced connections: servers inherit the root protocol and
authentication rather than their direct listener settings.

Unsupported `saml` authentication is skipped with a warning. An `oauth` scheme is
retained; add its bearer token before loading the environment. Review the output
for the access path your application will actually use.
