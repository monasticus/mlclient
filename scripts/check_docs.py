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
        self.signatures = []
        self._signature_depth = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        """Record anchors and links from a rendered HTML tag."""
        attrs = dict(attrs)
        if tag == "div":
            if self._signature_depth:
                self._signature_depth += 1
            elif "doc-signature" in attrs.get("class", "").split():
                self._signature_depth = 1
                self.signatures.append("")
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])


    def handle_endtag(self, tag):
        """Finish a signature when its enclosing div closes."""
        if tag == "div" and self._signature_depth:
            self._signature_depth -= 1

    def handle_data(self, data):
        """Collect visible signature text independently of syntax highlighting."""
        if self._signature_depth:
            self.signatures[-1] += data


# CLI guides describe the actual command surface without embedding help dumps.
for name, command in MLCLIentApplication().all().items():
    if not type(command).__module__.startswith("mlclient."):
        continue
    guide_path = Path("docs/cli", *name.split()).with_suffix(".md")
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


for path, page in pages.items():
    for signature in page.signatures:
        assert "Unpack[" not in "".join(signature.split()), (
            "Internal keyword schema in public signature", path, signature
        )

for name in ("HttpClient", "AsyncHttpClient"):
    path = site / "reference/mlclient/clients" / name / "index.html"
    assert pages[path].signatures, ("Missing constructor signature", path)
    signature = pages[path].signatures[0]
    assert f"{name}(*," in "".join(signature.split()), (
        "Forwarded constructor options must remain keyword-only", name
    )
    for parameter in ("protocol", "host", "port", "timeout", "config", "session_owner"):
        assert parameter in signature, ("Hidden constructor option", name, parameter)
    assert "kwargs" not in signature, ("Forwarded constructor options not expanded", name)


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

# Nested namespaces own public exports of their own.
for nested in (
    "mlclient.search.structured",
    "mlclient.search.options",
    "mlclient.search.sq",
    "mlclient.search.opt",
    "mlclient.services.diagnostics",
):
    documented[nested] = importlib.import_module(nested)

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
        identifier = f"{dotted}.{name}"
        if inspect.ismodule(obj):
            page = (site / "reference" / obj.__name__.replace(".", "/") / "index.html").resolve()
        elif dotted in {"mlclient.search.sq", "mlclient.search.opt"} and inspect.isclass(obj):
            identifier = f"{obj.__module__}.{obj.__qualname__}"
            assert seen.get((obj.__module__, obj.__qualname__)) == identifier, (
                f"Constructor alias has no canonical model export: {dotted}.{name}"
            )
            page = (site / "reference" / obj.__module__.replace(".", "/") / obj.__name__ / "index.html").resolve()
            assert any((index.parent / unquote(urlsplit(link).path)).resolve() in {page, page.parent} for link in pages[index].links), (
                f"Constructor alias has no model link: {dotted}.{name}"
            )
        elif inspect.isclass(obj) or inspect.isfunction(obj):
            identity = (obj.__module__, obj.__qualname__)
            assert identity not in seen, (
                f"Duplicate export: {dotted}.{name}, {seen.get(identity)}"
            )
            seen[identity] = f"{dotted}.{name}"
            page = (directory / name / "index.html").resolve()
        else:
            page = index
        assert page in pages, f"Missing API page: {dotted}.{name}"
        assert identifier in pages[page].ids, (
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
guide = (site / "guides/clients/index.html").read_text()
assert "<table>" in guide, "Authored Markdown tables must render as HTML tables"

client = (site / "reference/mlclient/MLClient/index.html").read_text()
for section in ("Parameters", "Returns", "Raises"):
    assert section in client, f"NumPy section missing: {section}"
sys.stdout.write(
    f"Validated {len(pages)} HTML pages, module coverage, links and API rendering\n",
)
