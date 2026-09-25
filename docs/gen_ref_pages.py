"""Generate reference pages from the canonical public exports."""

import importlib
import inspect
from pathlib import Path

import mkdocs_gen_files

root = Path(__file__).resolve().parent.parent
# Navigation owns namespaces; __all__ remains the sole inventory of symbols.
namespaces = (
    "mlclient",
    "mlclient.clients",
    "mlclient.env",
    "mlclient.http",
    "mlclient.auth",
    "mlclient.connection",
    "mlclient.models",
    "mlclient.api",
    "mlclient.calls",
    "mlclient.functions",
    "mlclient.functions.xqy",
    "mlclient.services",
    "mlclient.services.diagnostics",
    "mlclient.responses",
    "mlclient.multipart",
    "mlclient.io",
    "mlclient.exceptions",
    "mlclient.logging",
    "mlclient.jobs",
)
nav = mkdocs_gen_files.Nav()
# A dedicated landing page prevents section-index from consuming the first
# namespace together with its child pages (the root exports).
nav[("Overview",)] = "index.md"
with mkdocs_gen_files.open("reference/index.md", "w") as output:
    output.write(
        "# API reference\n\n"
        "Start with [MLClient](mlclient/MLClient.md), "
        "[AsyncMLClient](mlclient/AsyncMLClient.md), or "
        "[MLClientManager](mlclient/MLClientManager.md). "
        "Browse the namespaces for configuration, models and lower-level APIs.\n",
    )
for namespace in namespaces:
    module = importlib.import_module(namespace)
    directory = Path(*namespace.split("."))
    source = Path(module.__file__).relative_to(root)
    members = []
    values = []
    for name in module.__all__:
        obj = getattr(module, name)
        (members if inspect.isclass(obj) or inspect.isfunction(obj) else values).append(
            name,
        )
    index = directory / "index.md"
    body = f"# `{namespace}`\n\n"
    notice = getattr(module, "__experimental__", None)
    if notice:
        body += f'!!! warning "Experimental API"\n    {notice}\n\n'
    body += f"::: {namespace}\n    options:\n      members: "
    body += (
        "false\n"
        if not values
        else "\n" + "".join(f"        - {name}\n" for name in values)
    )
    with mkdocs_gen_files.open(Path("reference") / index, "w") as output:
        output.write(body)
    mkdocs_gen_files.set_edit_path(Path("reference") / index, Path("..") / source)
    nav[(namespace,)] = index.as_posix()
    for name in members:
        page = directory / f"{name}.md"
        with mkdocs_gen_files.open(Path("reference") / page, "w") as output:
            notice = getattr(getattr(module, name), "__experimental__", None)
            if notice:
                output.write(f'!!! warning "Experimental API"\n    {notice}\n\n')
            output.write(
                f"```python\nfrom {namespace} import {name}\n```\n\n"
                f"::: {namespace}.{name}\n",
            )
        mkdocs_gen_files.set_edit_path(Path("reference") / page, Path("..") / source)
        nav[(namespace, name)] = page.as_posix()

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as output:
    output.writelines(nav.build_literate_nav())
with mkdocs_gen_files.open("contributing.md", "w") as output:
    output.write((root / "CONTRIBUTING.md").read_text())
mkdocs_gen_files.set_edit_path("contributing.md", "../CONTRIBUTING.md")
