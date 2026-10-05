"""The Install Skill Command module.

It exports an implementation for 'install skill' command:
    * InstallSkillCommand
        Installs MLClient knowledge and templates for a coding agent.
"""

from __future__ import annotations

import json
import stat
import tempfile
from importlib.resources import files
from pathlib import Path

from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient.exceptions import WrongParametersError

_SKILL_DIRS = {
    "codex": ".agents/skills",
    "claude": ".claude/skills",
    "cursor": ".cursor/skills",
    "copilot": ".github/skills",
}


class InstallSkillCommand(Command):
    """Installs MLClient knowledge and templates for a coding agent.

    Copies the bundled skill into the selected agent's project or user directory.
    Reports file changes, preserves unrelated files and records the installation
    so ``self update`` can refresh it after upgrading MLClient.

    Usage:
      install skill [options] [--] [<agent>]

    Arguments:
      agent
            codex, claude, cursor or copilot. Omit to choose interactively.

    Options:
      -g, --global
            Install for the current user
      -f, --force
            Replace an existing MLClient installation
          --dry-run
            Show file changes without writing them
    """

    name: str = "install skill"
    description: str = "Install MLClient knowledge and templates for a coding agent"
    arguments: list[Argument] = [
        argument("agent", "codex, claude, cursor or copilot", optional=True),
    ]
    options: list[Option] = [
        option("global", "g", description="Install for the current user"),
        option("force", "f", description="Replace an existing MLClient installation"),
        option("dry-run", description="Show file changes without writing them"),
    ]

    def handle(self) -> int:
        """Install the requested skill and report every destination file.

        Returns
        -------
        int
            Zero after a successful installation or dry run.

        Raises
        ------
        WrongParametersError
            If the agent, registry or a destination is invalid or conflicts.
        OSError
            If reading or writing an installation file fails.
        """
        agent, root = self._resolve_target()
        _installation_records()
        target = _installation_path(
            agent, root, global_scope=self.option("global"),
        )
        self._apply_changes(_skill_changes(target))
        self._record_installation(agent, root)
        return 0

    def _resolve_target(self) -> tuple[str, Path]:
        """Resolve the selected agent and project or user scope.

        Returns
        -------
        tuple[str, Path]
            Supported agent identifier and installation root.

        Raises
        ------
        WrongParametersError
            If the selector is unsupported or missing in noninteractive mode.
        """
        agent = self.argument("agent")
        if agent is None and self.io.is_interactive():
            agent = self.choice("Install for which agent?", list(_SKILL_DIRS), 0)
        if agent not in _SKILL_DIRS:
            message = f"Choose an agent: {', '.join(_SKILL_DIRS)}."
            raise WrongParametersError(message)
        return agent, Path.home() if self.option("global") else Path.cwd()

    def _apply_changes(self, changes: dict[Path, bytes]) -> None:
        """Preflight every destination, report it, then write allowed changes.

        Parameters
        ----------
        changes : dict[Path, bytes]
            Proposed files with complete contents.

        Returns
        -------
        None
            Writes files unless dry-run is active, then reports session reload.

        Raises
        ------
        WrongParametersError
            If an existing installation conflicts, or a destination is a symlink.
        OSError
            If the destination cannot be read or written.
        """
        updates = {}
        for path, content in sorted(changes.items()):
            _check_destination(path)
            old = path.read_bytes() if path.exists() else None
            if old == content:
                self.line(f"Unchanged {Formatter.escape(str(path))}")
                continue
            if old is not None and not self.option("force"):
                message = (
                    f"Existing MLClient content in {path}; use --force to replace."
                )
                raise WrongParametersError(Formatter.escape(message))
            updates[path] = content
        verb = "Would write" if self.option("dry-run") else "Write"
        for path, content in updates.items():
            self.line(f"{verb} {Formatter.escape(str(path))}")
            if not self.option("dry-run"):
                _write_file(path, content)
        if self.option("dry-run"):
            self.line("Dry run: no files changed.")
        else:
            self.line("Restart the agent or start a new session to load MLClient.")

    def _record_installation(self, agent: str, root: Path) -> None:
        """Remember a successful installation so self-update can find other projects.

        Parameters
        ----------
        agent : str
            Supported agent identifier.
        root : Path
            Project or user installation root.

        Raises
        ------
        WrongParametersError
            If the installation registry is malformed or uses a symlink.
        OSError
            If reading or publishing the installation registry fails.
        """
        if self.option("dry-run"):
            return
        records = _installation_records()
        record = {
            "agent": agent,
            "root": str(root),
            "global": bool(self.option("global")),
        }
        if record not in records:
            records.append(record)
            path = Path.home() / ".mlclient/ai-installations.json"
            self.line(f"Write {Formatter.escape(str(path))} (installation record)")
            _write_file(path, (json.dumps(records, indent=2) + "\n").encode())


def find_installed_skills() -> list[dict]:
    """Find recorded skills plus user and ancestor-project installations.

    Returns
    -------
    list[dict]
        Existing agent/root/scope records, deduplicated by installation.

    Raises
    ------
    WrongParametersError
        If configuration is malformed or a skill path is a symlink.
    OSError
        If the registry or an installation cannot be inspected.
    """
    candidates = _installation_records()
    scopes = [(Path.home(), True)]
    scopes.extend((root, False) for root in (Path.cwd(), *Path.cwd().parents))
    candidates.extend(
        {"agent": agent, "root": str(root), "global": scope}
        for root, scope in scopes
        for agent in _SKILL_DIRS
    )
    existing = {}
    for record in candidates:
        path = _installation_path(
            record["agent"],
            Path(record["root"]),
            global_scope=record["global"],
        )
        path /= "SKILL.md"
        if not path.is_file():
            continue
        _check_destination(path)
        existing[str(path)] = record
    return list(existing.values())


def _installation_records() -> list[dict]:
    """Read recorded integration destinations without changing agent state.

    Returns
    -------
    list[dict]
        Validated agent, root and global-scope records.

    Raises
    ------
    WrongParametersError
        If the registry is malformed or uses a symlink destination.
    OSError
        If the registry cannot be read.
    """
    path = Path.home() / ".mlclient/ai-installations.json"
    _check_destination(path)
    if not path.exists():
        return []
    try:
        records = json.loads(path.read_text())
        valid = isinstance(records, list) and all(
            isinstance(record, dict)
            and set(record) == {"agent", "root", "global"}
            and record["agent"] in _SKILL_DIRS
            and isinstance(record["root"], str)
            and Path(record["root"]).is_absolute()
            and isinstance(record["global"], bool)
            for record in records
        )
        if valid:
            return records
    except (ValueError, TypeError):
        pass
    message = f"Invalid AI installation registry: {path}"
    raise WrongParametersError(Formatter.escape(message))


def _installation_path(agent: str, root: Path, *, global_scope: bool) -> Path:
    """Resolve the skill directory for project or user scope.

    Parameters
    ----------
    agent : str
        Supported agent identifier.
    root : Path
        Project or user root.
    global_scope : bool
        Whether to select user rather than project locations.

    Returns
    -------
    Path
        Skill directory.
    """
    relative = _SKILL_DIRS[agent]
    if global_scope and agent == "copilot":
        relative = ".copilot/skills"
    return root / relative / "mlclient"


def _skill_changes(target: Path) -> dict[Path, bytes]:
    """Read the complete bundled skill as destination-to-content pairs.

    Parameters
    ----------
    target : Path
        Destination skill directory.

    Returns
    -------
    dict[Path, bytes]
        All skill files, including references and executable templates.

    Raises
    ------
    OSError
        If a bundled directory or file cannot be read.
    """
    source = files("mlclient").joinpath("resources", "skills", "mlclient")
    pending = [(source, target)]
    changes = {}
    while pending:
        directory, destination = pending.pop()
        for child in sorted(directory.iterdir(), key=lambda item: item.name):
            path = destination / child.name
            if child.is_dir():
                pending.append((child, path))
            else:
                changes[path] = child.read_bytes()
    return changes


def _check_destination(path: Path) -> None:
    """Reject symlink destinations before reading or writing agent state.

    Parameters
    ----------
    path : Path
        File or directory to check, including every parent directory.

    Raises
    ------
    WrongParametersError
        If the destination or one of its parents is a symbolic link.
    """
    if any(part.is_symlink() for part in (path, *path.parents)):
        message = f"Refusing symlink destination {path}."
        raise WrongParametersError(Formatter.escape(message))


def _write_file(path: Path, content: bytes) -> None:
    """Replace one file atomically, preserving existing permissions.

    Parameters
    ----------
    path : Path
        Destination file; parent directories are created as needed.
    content : bytes
        Complete contents to publish. New files are accessible only to the user.

    Raises
    ------
    OSError
        If staging or replacement fails. The staging file is removed and an
        existing destination remains intact when replacement fails.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        staging = Path(temporary.name)
        try:
            temporary.write(content)
            temporary.flush()
            staging.chmod(mode)
            staging.replace(path)
        finally:
            staging.unlink(missing_ok=True)
