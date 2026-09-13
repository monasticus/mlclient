import subprocess

import pytest

from scripts import release


@pytest.mark.parametrize("version", ["1.0.0", "1.2.3rc1", "1.0.0b0", "2.0.0a12"])
def test_accepts_canonical_release_versions(version):
    assert release.validate_version(version) == version


@pytest.mark.parametrize(
    "version", ["v1.0.0", "1.0", "01.0.0", "1.0.0-dev", "1.0.0+local", "1.0.0rc01"],
)
def test_rejects_nonrelease_versions(version):
    with pytest.raises(ValueError, match=r"Expected X\.Y\.Z"):
        release.validate_version(version)


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    root.mkdir()
    monkeypatch.setattr(release, "ROOT", root)
    release.run("git", "init", "-b", "main")
    release.run("git", "config", "user.email", "test@example.com")
    release.run("git", "config", "user.name", "Release test")
    (root / "mlclient").mkdir()
    (root / "mlclient/__init__.py").write_text('__version__ = "1.0.0"\n')
    (root / "pyproject.toml").write_text('[tool.poetry]\nversion = "1.0.0"\n')
    release.run("git", "add", ".")
    release.run("git", "commit", "-m", "Initial version")
    remote = tmp_path / "origin.git"
    release.run("git", "init", "--bare", str(remote))
    release.run("git", "remote", "add", "origin", str(remote))
    release.run("git", "push", "-u", "origin", "main")
    original_run = release.run

    def run(*args):
        if args[0] == "poetry":
            return "1.0.0"
        return original_run(*args)

    monkeypatch.setattr(release, "run", run)
    return root


@pytest.mark.usefixtures("checkout")
def test_tags_clean_reviewed_main_and_rejects_existing_tag():
    release.tag_release()
    assert "refs/tags/1.0.0" in release.run("git", "ls-remote", "--tags", "origin")
    with pytest.raises(ValueError, match="already exists"):
        release.tag_release()


def test_refuses_dirty_checkout_before_pushing(checkout):
    (checkout / "unrelated.txt").write_text("Do not include me")
    with pytest.raises(ValueError, match="clean working tree"):
        release.tag_release()
    assert not release.run("git", "tag", "--list")


@pytest.mark.usefixtures("checkout")
def test_refuses_feature_branch():
    release.run("git", "switch", "-c", "feature/test")
    with pytest.raises(ValueError, match="Switch to main"):
        release.tag_release()


@pytest.mark.usefixtures("checkout")
def test_refuses_unpushed_main():
    release.run("git", "commit", "--allow-empty", "-m", "Not reviewed")
    with pytest.raises(ValueError, match="must match origin/main"):
        release.tag_release()


def test_tag_must_match_exported_version(checkout):
    with pytest.raises(ValueError, match="Release tag must match"):
        release.verify_tag("1.0.1")
    (checkout / "mlclient/__init__.py").write_text('__version__ = "0.4.1"\n')
    with pytest.raises(ValueError, match="versions differ"):
        release.verify_tag("1.0.0")


@pytest.mark.usefixtures("checkout")
def test_tag_commit_must_be_on_main():
    release.run("git", "switch", "-c", "feature/unreviewed")
    release.run("git", "commit", "--allow-empty", "-m", "Not reviewed")
    with pytest.raises(subprocess.CalledProcessError):
        release.verify_tag("1.0.0")


@pytest.mark.parametrize("version", ["1.0.1", "patch", "v1.1.0rc1"])
def test_prerelease_target_requires_explicit_candidate(version):
    with pytest.raises(ValueError, match=r"requires an explicit|Expected"):
        release.prepare(version, prerelease=True)


def test_prepare_pushes_only_version_branch(checkout, monkeypatch):
    original_run = release.run
    commands = []

    def run(*args):
        commands.append(args)
        if args[0] == "poetry":
            if "--dry-run" in args:
                return "1.1.0"
            if args[-1] == "1.1.0":
                for file in ("pyproject.toml", "mlclient/__init__.py"):
                    path = checkout / file
                    path.write_text(path.read_text().replace("1.0.0", "1.1.0"))
                return ""
            return "1.1.0" if any("--dry-run" in item for item in commands) else "1.0.0"
        if args[0] == "gh":
            return "https://example.com/pr/1"
        return original_run(*args)

    monkeypatch.setattr(release, "run", run)
    original_main = release.run("git", "rev-parse", "origin/main")
    release.prepare("minor")
    assert release.run("git", "branch", "--show-current") == "feature/release-1.1.0"
    assert release.run("git", "rev-parse", "origin/main") == original_main
    assert not release.run("git", "tag", "--list")
    assert ("git", "push", "-u", "origin", "feature/release-1.1.0") in commands
    assert any(command[:3] == ("gh", "pr", "create") for command in commands)
