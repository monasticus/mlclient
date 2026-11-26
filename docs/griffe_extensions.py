"""Adapt legacy documentation syntax during rendering without editing source."""

import re

from griffe import (Attribute, DocstringSectionKind, DocstringSectionText,
                    ExprName, ExprSubscript, Extension, Function, Parameter,
                    ParameterKind, Parameters, UnpackTypedDictExtension)


class LegacyDocstrings(Extension):
    """Render public signatures, forwarded options and legacy help text."""

    _unpack = UnpackTypedDictExtension()

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

    def on_function(self, *, func, **kwargs):
        """Expand shared keyword schemas and preserve their calling context."""
        for signature in (func, *(func.overloads or [])):
            parameter = _unpacked_parameter(signature)
            if parameter is None:
                continue
            schema = signature.modules_collection[parameter.annotation.slice.canonical_path]
            _include_inherited_fields(schema)
            description = ""
            sections = signature.docstring.parsed if signature.docstring else []
            position = len(sections)
            for position, section in enumerate(sections):
                if section.kind is DocstringSectionKind.parameters:
                    description = next(
                        (item.description for item in section.value
                         if item.name.lstrip("*") == parameter.name),
                        "",
                    )
                    break
            text = (description + "\n\n" if description else "") + (
                "Expanded keyword defaults shown as `...` mean the keyword "
                "is omitted; the operation's defaults and inheritance apply. "
                "An explicit `None` keeps its documented meaning."
            )
            self._unpack.on_function(func=signature, **kwargs)
            signature.docstring.parsed.insert(position, DocstringSectionText(text))

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


def _unpacked_parameter(function):
    """Find the function's standard TypedDict keyword expansion, if present."""
    for parameter in function.parameters:
        annotation = parameter.annotation
        if (
            parameter.kind is ParameterKind.var_keyword
            and isinstance(annotation, ExprSubscript)
            and annotation.canonical_path in {"typing.Unpack", "typing_extensions.Unpack"}
        ):
            return parameter
    return None


def _include_inherited_fields(schema):
    """Expose inherited schema fields to Griffe's own-field unpacking extension."""
    inherited = {}
    for name, alias in schema.inherited_members.items():
        if name in schema.members or not alias.is_attribute:
            continue
        field = alias.final_target
        annotation = field.annotation
        inner = annotation
        if isinstance(inner, ExprSubscript) and inner.canonical_path in {
            "typing.ReadOnly", "typing_extensions.ReadOnly",
        }:
            inner = inner.slice
        if not (
            isinstance(inner, ExprSubscript)
            and inner.canonical_path in {
                "typing.Required", "typing_extensions.Required",
                "typing.NotRequired", "typing_extensions.NotRequired",
            }
        ):
            required = str(field.parent.keywords.get("total", "True")) != "False"
            qualifier = "Required" if required else "NotRequired"
            annotation = ExprSubscript(
                left=ExprName(name=f"typing.{qualifier}"), slice=annotation,
            )
        inherited[name] = Attribute(
            name, annotation=annotation, docstring=field.docstring,
        )
    if inherited:
        members = {**inherited, **schema.members}
        schema.members.clear()
        for name, member in members.items():
            schema.set_member(name, member)
