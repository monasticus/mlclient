"""Prepare a reviewed version change, validate release tags, or tag merged main."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from packaging.version import Version


ROOT = Path(__file__).resolve().parent.parent


def run(*args: str) -> str:
    """Run a command in the checkout and return its output, failing on errors."""
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def validate_version(value: str) -> str:
    """Require a canonical bare X.Y.Z version, optionally with a/b/rc suffix."""
    if not re.fullmatch(
        r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:(a|b|rc)(0|[1-9]\d*))?",
        value,
    ):
        msg = f"Expected X.Y.Z or X.Y.ZrcN/aN/bN, without a v prefix: {value}"
        raise ValueError(msg)
    return value


def project_version() -> str:
    """Read the Poetry version and ensure the exported version matches it."""
    version = validate_version(run("poetry", "version", "--short"))
    source = (ROOT / "mlclient/__init__.py").read_text()
    match = re.search(r'^__version__ = "([^"]+)"$', source, re.MULTILINE)
    if match is None or match[1] != version:
        msg = "Package/source versions differ; install the Poetry bumpversion plugin."
        raise ValueError(msg)
    return version


def require_clean_main() -> None:
    """Require a clean main checkout identical to fetched origin/main."""
    if run("git", "status", "--porcelain"):
        msg = "Release preparation requires a clean working tree."
        raise ValueError(msg)
    if run("git", "branch", "--show-current") != "main":
        msg = "Switch to main before preparing or tagging a release."
        raise ValueError(msg)
    run("git", "fetch", "origin", "main", "--tags")
    if run("git", "rev-parse", "HEAD") != run("git", "rev-parse", "origin/main"):
        msg = "Local main must match origin/main; update it before continuing."
        raise ValueError(msg)


def verify_tag(tag: str) -> None:
    """Reject mismatched versions and release commits outside origin/main."""
    if validate_version(tag) != project_version():
        msg = "Release tag must match both package and source versions."
        raise ValueError(msg)
    run("git", "merge-base", "--is-ancestor", "HEAD", "origin/main")


def prepare(bump: str, *, prerelease: bool = False) -> None:
    """Push a version-only branch for review; never commit directly to main."""
    if prerelease and not Version(validate_version(bump)).is_prerelease:
        msg = "release-pre requires an explicit a, b or rc version."
        raise ValueError(msg)
    require_clean_main()
    current = project_version()
    # Poetry supplies version arithmetic; no second versioning implementation.
    version = validate_version(
        run("poetry", "--no-plugins", "version", bump, "--dry-run", "--short"),
    )
    if Version(version) <= Version(current):
        msg = "The prepared version must be newer than the current version."
        raise ValueError(msg)
    if run("git", "tag", "--list", version):
        msg = f"Tag {version} already exists."
        raise ValueError(msg)
    branch = f"feature/release-{version}"
    run("git", "switch", "-c", branch)
    run("poetry", "version", version)
    project_version()
    metadata = ROOT / "pyproject.toml"
    stage = "4 - Beta" if Version(version).is_prerelease else "5 - Production/Stable"
    if Version(version).major >= 1:
        metadata.write_text(
            re.sub(
                r"Development Status :: [^\"]+",
                f"Development Status :: {stage}",
                metadata.read_text(),
            ),
        )
    run("git", "add", "pyproject.toml", "mlclient/__init__.py")
    run("git", "commit", "-m", f"Prepare release {version}")
    run("git", "push", "-u", "origin", branch)
    run(
        "gh",
        "pr",
        "create",
        "--base",
        "main",
        "--head",
        branch,
        "--title",
        f"Prepare release {version}",
        "--body",
        f"Synchronize package and source versions for {version}. "
        "Squash-merge after required checks pass, then run make release-tag on main.",
    )


def tag_release() -> None:
    """Push an annotated tag for a reviewed version already merged into main."""
    require_clean_main()
    version = project_version()
    if run("git", "tag", "--list", version):
        msg = f"Tag {version} already exists; rerun CI rather than moving the tag."
        raise ValueError(msg)
    run("git", "tag", "-a", version, "-m", f"Release {version}")
    run("git", "push", "origin", f"refs/tags/{version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "tag", "verify"])
    parser.add_argument("version", nargs="?")
    parser.add_argument("--prerelease", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "tag":
            tag_release()
        elif args.version is None:
            parser.error("prepare and verify require a version or bump rule")
        elif args.action == "prepare":
            prepare(args.version, prerelease=args.prerelease)
        else:
            verify_tag(args.version)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Release stopped: {error}\n")
