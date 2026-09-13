"""Check the built site's module coverage, links and representative API output."""

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    """Collect HTML identifiers and internal link targets."""

    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])


site = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
pages = {path: Page(path.read_text()) for path in site.rglob("*.html")}
assert pages, "Build the site before running this check"
for source in Path("mlclient").rglob("*.py"):
    if source.name == "__main__.py":
        continue
    module = source.with_suffix("")
    if source.name == "__init__.py":
        module = module.parent
    expected = site / "reference" / module / "index.html"
    assert expected in pages, f"Missing API page for {source}"

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

model = (site / "reference/mlclient/ml_environment/index.html").read_text()
for marker in ("Show JSON schema:", "_ensure_default_app_servers", '"properties"'):
    # Schema JSON may be HTML-escaped by syntax highlighting.
    assert marker in model or marker.replace('"', '&quot;') in model, marker
guide = (site / "user/pythonapi/index.html").read_text()
assert "<table>" in guide, "Authored Markdown tables must render as HTML tables"

client = (site / "reference/mlclient/clients/ml_client/index.html").read_text()
for section in ("Parameters", "Returns", "Raises"):
    assert section in client, f"NumPy section missing: {section}"
print(f"Validated {len(pages)} HTML pages, module coverage, links and API rendering")
