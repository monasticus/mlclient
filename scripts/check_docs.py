"""Check the built site's module coverage, links and representative API output."""

import importlib
import inspect
import pkgutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import mlclient
from mlclient.cli import MLCLIentApplication


class Page(HTMLParser):
    """Collect HTML identifiers and internal link targets."""

    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        """Record anchors and links from a rendered HTML tag."""
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])


# CLI guides describe the actual command surface without embedding help dumps.
for name, command in MLCLIentApplication().all().items():
    if not type(command).__module__.startswith("mlclient."):
        continue
    guide_path = Path("docs/user/cli", *name.split()).with_suffix(".md")
    guide_text = guide_path.read_text()
    assert "Description:\n" not in guide_text, f"Help dump in {guide_path}"
    for argument in command.definition.arguments:
        assert f"### `{argument.name}`" in guide_text, (name, argument.name)
    for option in command.definition.options:
        heading = f"### `--{option.name}`"
        if option.shortcut:
            heading += f", `-{option.shortcut}`"
        assert heading in guide_text, (name, option.name)


site = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
pages = {path: Page(path.read_text()) for path in site.rglob("*.html")}
assert pages, "Build the site before running this check"


# Only top-level public modules/packages define canonical user imports.
# The CLI is an executable entry point, not part of the Python library reference.
documented = {"mlclient": mlclient}
for info in pkgutil.iter_modules(mlclient.__path__, "mlclient."):
    leaf = info.name.rsplit(".", 1)[-1]
    if leaf.startswith("_") or leaf in {"cli", "resources"}:
        continue
    module = importlib.import_module(info.name)
    assert hasattr(module, "__all__"), f"Missing public export contract: {info.name}"
    documented[info.name] = module

# Language-specific function namespaces own their public builder exports.
documented["mlclient.functions.xqy"] = importlib.import_module("mlclient.functions.xqy")

# Root exports must be reachable from the rendered navigation, not merely built.
home = pages[site / "index.html"]
for name in ("MLClient", "AsyncMLClient", "MLClientManager"):
    assert f"reference/mlclient/{name}/" in home.links, f"Root export hidden: {name}"

seen = {}
for dotted, module in documented.items():
    directory = site / "reference" / dotted.replace(".", "/")
    index = (directory / "index.html").resolve()
    assert index in pages, f"Missing namespace page: {dotted}"
    for name in module.__all__:
        obj = getattr(module, name)
        if inspect.isclass(obj) or inspect.isfunction(obj):
            identity = (obj.__module__, obj.__qualname__)
            assert identity not in seen, (
                f"Duplicate export: {dotted}.{name}, {seen.get(identity)}"
            )
            seen[identity] = f"{dotted}.{name}"
            page = (directory / name / "index.html").resolve()
        else:
            page = index
        assert page in pages, f"Missing API page: {dotted}.{name}"
        assert f"{dotted}.{name}" in pages[page].ids, (
            f"Missing canonical anchor: {dotted}.{name}"
        )
        if getattr(obj, "__experimental__", None):
            rendered = page.read_text()
            assert "admonition warning" in rendered, (dotted, name)
            assert "Experimental API" in rendered, (dotted, name)


for source, page in pages.items():
    for href in page.links:
        url = urlsplit(href)
        if url.scheme or url.netloc or href.startswith("/"):
            continue
        target = (source.parent / unquote(url.path)).resolve() if url.path else source
        if target.is_dir():
            target /= "index.html"
        assert target.exists(), f"Broken link in {source.relative_to(site)}: {href}"
        if url.fragment and target in pages:
            assert unquote(url.fragment) in pages[target].ids, (
                f"Missing anchor in {source.relative_to(site)}: {href}"
            )

model = (site / "reference/mlclient/env/MLEnvironment/index.html").read_text()
for marker in ("Show JSON schema:", "_ensure_default_app_servers", '"properties"'):
    # Schema JSON may be HTML-escaped by syntax highlighting.
    assert marker in model or marker.replace('"', "&quot;") in model, marker
guide = (site / "user/clients/index.html").read_text()
assert "<table>" in guide, "Authored Markdown tables must render as HTML tables"

client = (site / "reference/mlclient/MLClient/index.html").read_text()
for section in ("Parameters", "Returns", "Raises"):
    assert section in client, f"NumPy section missing: {section}"
sys.stdout.write(
    f"Validated {len(pages)} HTML pages, module coverage, links and API rendering\n",
)
