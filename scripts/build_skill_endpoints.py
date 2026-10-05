"""Build the bundled endpoint reference from local MarkLogic documentation.

Run: python scripts/build_skill_endpoints.py /path/to/marklogic/source-docs
The source documents are the v10-v12 LLM REST API reference exports.
"""

import ast
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "mlclient/resources/skills/mlclient/references/endpoints"


def normalized(path):
    """Compare endpoint patterns independently of placeholder spelling."""
    return re.sub(r"\{[^}]+\}|\[[^]]+\]", "{}", path.split("?", 1)[0])


def wrappers():
    """Index public sync API methods by their official documentation URL."""
    result = {}
    for path in sorted((ROOT / "mlclient/api").glob("*.py")):
        tree = ast.parse(path.read_text())
        for cls in tree.body:
            if not isinstance(cls, ast.ClassDef) or cls.name.startswith("Async"):
                continue
            for method in cls.body:
                if not isinstance(method, ast.FunctionDef):
                    continue
                doc = ast.get_docstring(method) or ""
                match = re.search(r"https://docs.marklogic.com/REST/(\w+)(/\S+)", doc)
                if not match:
                    continue
                verb, endpoint = match.groups()
                tier = "manage" if path.stem in {"databases", "forests", "groups", "hosts", "logs", "roles", "servers", "users"} else "rest"
                if path.stem == "admin":
                    tier = "admin"
                name = f"ml.{tier}.{path.stem}.{method.name}"
                if tier == "admin":
                    name = f"ml.admin.{method.name}"
                result[(verb, normalized(endpoint))] = (name, endpoint, ast.unparse(method.args))
    return result


def build(source_root):
    """Preserve every endpoint contract and add per-version library routing."""
    TARGET.mkdir(parents=True, exist_ok=True)
    known = wrappers()
    for version in (10, 11, 12):
        source = source_root / f"v{version}/llm/marklogic-rest-api-reference-{version}.md"
        text = re.sub(
            r"(?m)^[ \t]+",
            lambda match: match.group().expandtabs(),
            source.read_text(),
        )
        matches = list(re.finditer(r"^## (GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS) (.+)$", text, re.M))
        output = f"# MarkLogic {version} endpoint contracts\n\n"
        output += "Bundled from the MarkLogic REST API Reference export supplied with the Palamentis knowledge base.\n"
        output += "Vendor contract text is preserved; MLClient routes and links are generated from this checkout.\n\n"
        rows = []
        for i, match in enumerate(matches):
            verb, endpoint = match.groups()
            key = (verb, normalized(endpoint))
            wrapper = known.get(key)
            route = f"`{wrapper[0]}` (sync and async)" if wrapper else "Raw HTTP / custom ApiCall"
            if wrapper and "?" in endpoint:
                route += "; pass the documented query parameter (check wrapper validation)"
            start = output.count("\n") + 1
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            chunk = "\n".join(line.rstrip() for line in text[match.start():end].splitlines()).rstrip()
            # Section boundaries, including original family headings, stay intact.
            output += chunk + ("\n\n" if i + 1 < len(matches) else "\n")
            stop = output.count("\n")
            rows.append(f"| `{verb} {endpoint.replace('|', '&#124;')}` | {route} | {start}-{stop} |")
        (TARGET / f"v{version}.md").write_text(output)
        index = f"# MarkLogic {version}: {len(matches)} endpoint contracts\n\n"
        index += f"Read only the relevant section of `v{version}.md`, using the inclusive line ranges below.\n"
        index += "Every row includes all supplied parameters, request/response headers, response description, privileges, usage and examples where present in the vendor export.\n"
        index += "A wrapper covers the operation, not necessarily every parameter or view; use raw HTTP when its signature or validator is narrower.\n\n"
        index += "| Endpoint | MLClient route | Lines |\n| --- | --- | --- |\n" + "\n".join(rows) + "\n"
        (TARGET / f"v{version}-index.md").write_text(index)
    api = "# Named API methods\n\nUse the same methods with `await` on AsyncMLClient. Parameters below are actual Python signatures; `timeout` controls transport, not endpoint query data.\n\n"
    for (verb, _), (name, path, signature) in sorted(known.items()):
        url = f"https://docs.marklogic.com/12.0/REST/{verb}{quote(path, safe='/@()|=')}"
        api += f"## `{name}`\n\n`{verb} {path}`\n\n```python\n{signature}\n```\n\n[MarkLogic 12 contract]({url})\n\n"
    (TARGET.parent / "api-methods.md").write_text(api.rstrip() + "\n")
    print(f"Generated contracts for MarkLogic 10, 11, 12; {len(known)} named API methods.")


if __name__ == "__main__":
    build(Path(sys.argv[1]))
