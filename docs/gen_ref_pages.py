"""Generate API pages from every package module without maintaining stubs."""

from pathlib import Path

import mkdocs_gen_files

root = Path(__file__).resolve().parent.parent
nav = mkdocs_gen_files.Nav()
for path in sorted((root / "mlclient").rglob("*.py")):
    module = path.relative_to(root).with_suffix("")
    parts = list(module.parts)
    page = module.with_suffix(".md")
    if parts[-1] == "__main__":
        continue
    if parts[-1] == "__init__":
        parts.pop()
        page = page.with_name("index.md")
    nav[parts] = page.as_posix()
    destination = Path("reference") / page
    with mkdocs_gen_files.open(destination, "w") as output:
        output.write(f"::: {'.'.join(parts)}\n")
    mkdocs_gen_files.set_edit_path(destination, Path("..") / path.relative_to(root))

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as output:
    output.writelines(nav.build_literate_nav())

# Publish the repository contribution guide without maintaining a second copy.
with mkdocs_gen_files.open("contributing.md", "w") as output:
    output.write((root / "CONTRIBUTING.md").read_text())
mkdocs_gen_files.set_edit_path("contributing.md", "../CONTRIBUTING.md")
