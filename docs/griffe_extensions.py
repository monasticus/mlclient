"""Adapt legacy documentation syntax during rendering without editing source."""

import re

from griffe import (ExprSubscript, Extension, Function, Parameter,
                    ParameterKind, Parameters)


class LegacyDocstrings(Extension):
    """Render public signatures, forwarded options and legacy help text."""

    def on_members(self, *, obj, **kwargs):
        """Render accepted options after functions and overloads are collected."""
        for member in obj.members.values():
            if not isinstance(member, Function) or not member.path.startswith("mlclient."):
                continue
            if member.path in {
                "mlclient.clients.http.HttpClient.__init__",
                "mlclient.clients.http.AsyncHttpClient.__init__",
            }:
                base = member.module.members["_HttpClientBase"].members["__init__"]
                member.parameters = Parameters(
                    *(
                        Parameter(
                            parameter.name,
                            annotation=parameter.annotation,
                            kind=(
                                parameter.kind
                                if parameter.name == "self"
                                else ParameterKind.keyword_only
                            ),
                            default=parameter.default,
                        )
                        for parameter in base.parameters
                    ),
                )
            for signature in (member, *(member.overloads or [])):
                for parameter in signature.parameters:
                    annotation = parameter.annotation
                    if (
                        parameter.kind is ParameterKind.var_keyword
                        and isinstance(annotation, ExprSubscript)
                        and str(annotation.left).rsplit(".", 1)[-1] == "Unpack"
                    ):
                        parameter.annotation = None

    def on_object(self, *, obj, **kwargs):
        """Adapt the documentation model without changing the Python API."""
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
            "mlclient.clients.http.HttpClient.__init__",
            "mlclient.clients.http.AsyncHttpClient.__init__",
        }:
            # These constructors expose **kwargs and document forwarded options.
            obj.docstring.parser_options["warn_unknown_params"] = False
