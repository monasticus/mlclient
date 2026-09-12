"""Adapt legacy documentation syntax during rendering without editing source."""

import re

from griffe import Extension


class LegacyDocstrings(Extension):
    """Render Cleo help literally and allow documented forwarded kwargs."""

    def on_object(self, *, obj, **kwargs):
        """Adapt only documentation constructs with different Markdown meaning."""
        if not obj.docstring:
            return
        if obj.path.startswith("mlclient.cli.commands."):
            # Cleo's [--] and [<setting>] are syntax, not Markdown references.
            obj.docstring.value = re.sub(
                r"(?m)^Usage:\n([\s\S]*)$",
                lambda match: "```text\nUsage:\n" + match[1] + "\n```",
                obj.docstring.value,
            )
        if obj.path in {
            "mlclient.clients.http_client.HttpClient.__init__",
            "mlclient.clients.http_client.AsyncHttpClient.__init__",
        }:
            # These constructors expose **kwargs and document forwarded options.
            obj.docstring.parser_options["warn_unknown_params"] = False
