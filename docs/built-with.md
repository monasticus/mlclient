# Built with

MLClient uses these open-source tools for its library, CLI and development
workflow. Thanks to their maintainers and contributors.

- **Project management -- [Poetry](https://python-poetry.org/).** Dependency
  resolution, virtual environments, packaging and the build backend.
- **HTTP -- [HTTPX](https://www.python-httpx.org/).** The HTTP client behind
  every request, giving MLClient both synchronous and `asyncio` transports from
  one API.
- **CLI -- [Cleo](https://github.com/python-poetry/cleo).** The framework behind
  the `ml` command-line interface: commands, arguments, prompts and styled
  output.
- **Format and lint -- [Ruff](https://docs.astral.sh/ruff/).** Linting and code
  formatting in a single fast pass, shared between local development and CI.
- **Docs -- [MkDocs](https://www.mkdocs.org/) with
  [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).** This
  documentation site; the API reference is generated from docstrings by
  [mkdocstrings](https://mkdocstrings.github.io/).
