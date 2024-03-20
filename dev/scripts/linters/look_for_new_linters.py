#!/usr/bin/python3

import json
import subprocess
from pathlib import Path


def main():
    known_linters = _get_known_linters()
    latest_linters = _get_latest_linters()
    diff = _get_difference(known_linters, latest_linters)
    _print_result(diff)


def _get_known_linters():
    linters = Path("dev/scripts/linters/linters.json").read_text()
    return json.loads(linters)


def _get_latest_linters(
) -> list:
    linters = subprocess.check_output(["ruff", "linter", "--output-format=json"])
    return json.loads(linters)


def _get_difference(
        known_linters: list,
        latest_linters: list,
) -> list:
    return [linter for linter in latest_linters if linter not in known_linters]


def _print_result(
        diff
):
    if len(diff) > 0:
        print("New linters have arrived:")
        _print_missing_linters(diff)
    else:
        print("You know all linters already.")


def _print_missing_linters(
        diff
):
    for linter in diff:
        info = _get_linter_info(linter)
        print(info)


def _get_linter_info(
        linter: dict,
) -> str:
    prefix = linter.get("prefix")
    name = linter.get("name")
    categories = linter.get("categories")
    base_info = f"  {prefix}: {name}"
    if categories is None:
        return f"  {prefix}: {name}"

    return _get_linter_categories_info(base_info, categories)


def _get_linter_categories_info(
        base_info,
        categories,
) -> str:
    categories_info = ", ".join([f"{category['prefix']}: {category['name']}"
                                 for category in categories])
    return f"{base_info} [{categories_info}]"


if __name__ == "__main__":
    main()
