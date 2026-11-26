"""Check installed-package type hints from a consumer's point of view.

Valid examples must type-check with their expected inferred types. Invalid
examples must fail at the marked lines with the expected mypy error categories.
Neither fixture is executed; mypy analyzes it outside the source checkout.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Require valid consumers to pass and invalid consumers to fail precisely."""
    with tempfile.TemporaryDirectory(prefix="mlclient-typing-") as directory:
        target = Path(directory)
        for name in ("valid.py", "invalid.py"):
            source = ROOT / "tests" / "typing" / name
            shutil.copyfile(source, target / name)
            result = subprocess.run(
                [
                    sys.executable, "-m", "mypy", "--config-file",
                    str(ROOT / "pyproject.toml"), "--no-incremental",
                    "--no-error-summary", name,
                ],
                cwd=target, capture_output=True, text=True, check=False,
            )
            expected = {
                (number, match[1])
                for number, line in enumerate(source.read_text().splitlines(), 1)
                if (match := re.search(r"# error: ([\w-]+)", line))
            }
            actual = {
                (int(match[1]), match[2])
                for line in result.stdout.splitlines()
                if (match := re.match(r"[^:]+:(\d+): error: .*\[([\w-]+)\]$", line))
            }
            if actual != expected or result.returncode != bool(expected):
                message = f"Typing contract failed for {name}:\n{result.stdout}{result.stderr}"
                raise RuntimeError(message)
    print("Consumer typing contracts passed.")


if __name__ == "__main__":
    main()
