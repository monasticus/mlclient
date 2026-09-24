# trace-events

Show or change a group's diagnostic trace events: the master "Trace Events
Activated" switch and the set of enabled trace events shown on the Admin
Interface Diagnostics page.

```sh
ml trace-events
ml trace-events true
```

Without a value the command shows the group's state:

```text
Group: Default
Trace Events Activated: true

Optic Query Parsing: on
XDMP Deadlock: on
```

A bare value sets the master switch:

```text
Group: Default
Trace Events Activated: true
```

Show or toggle a single event with `--event`. With a value it adds the event
(truthy) or removes it (falsy); without a value it shows that event's status:

```sh
ml trace-events --event "XDMP Deadlock"
ml trace-events -E "XDMP Deadlock" on
ml trace-events --event "XDMP Deadlock" off
```

```text
Group: Default
Trace Events Activated: true
XDMP Deadlock: on
```

Choose the switch and prune the enabled events at prompts:

```sh
ml trace-events -i
```

The command evaluates Admin module functions through the selected REST
connection and saves the configuration when a value changes it.

An event shown as `on` is in the configured set; it only emits traces when the
master activation switch is also `true`. Changing one event does not change
that switch. Repeating an add or removal is safe, including when the event is
already present or absent.

The selected connection needs permission to evaluate XQuery and use the Admin
group functions. Saving additionally requires the configuration-write privilege;
see [Admin group privileges](https://docs.marklogic.com/admin:group-get-trace-events)
and [configuration-save privileges](https://docs.marklogic.com/admin:save-configuration).
Failures return a nonzero exit code. There is no Manage API fallback.

Each change is saved and then read back in a separate request. An error during
that read does not undo the saved change. Interactive edits also use separate
saves, so a later failure can leave earlier changes applied. Inspect the state
with `ml trace-events` before retrying. When turning tracing on, unchecked events
are removed first; when turning it off, the master switch is disabled first.

## Arguments

### `value`

Optional boolean. On its own it sets Trace Events Activated; with `--event` it
adds the event (truthy) or removes it (falsy). Omit it to read the current
state. Accepts `true`/`false`, `on`/`off`, `1`/`0` or `yes`/`no`.

## Options

### `--group`, `-g`

MarkLogic group name. Defaults to `Default`.

### `--event`, `-E`

A single trace event name. On its own it shows that event's status; with a
value it adds or removes the event.

### `--interactive`, `-i`

Prompt for the activation switch and the enabled events instead of taking a
value. The event prompt lists the currently enabled events, all pre-selected;
unselecting one removes it. Adding a new event still uses `--event <name> on`.
Cannot be combined with `value`, `--event` or `--no-interaction` (`-n`). It requires
interactive input; use explicit values in scripts. Cancelling applies no changes.

### `--environment`, `-e`

Environment name. Defaults to `local`; use `-e dev` to load
`.mlclient/mlclient-dev.yaml`.

### `--connection`, `-c`

Configured connection identifier or TCP port (`1`–`65535`). Omit it to use the
default REST connection. A port changes that connection's port and retains its
other settings. For example, `-c content` selects a named connection and
`-c 8100` uses port 8100.

See also [global options](../cli.md#global-options).
