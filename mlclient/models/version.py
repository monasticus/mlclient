"""Lossless MarkLogic server version representation."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MarkLogicVersion:
    """An immutable server version with four numeric parts.

    Parameters
    ----------
    raw : str
        Dotted or legacy hyphenated version, e.g. ``12.0.1`` or ``10.0-9.5``.
        Surrounding whitespace is removed; separators and suffixes are preserved.

    Attributes
    ----------
    parts : tuple[int, int, int | None, int | None]
        Numeric components in their original order. Missing components are None.
        Iterating or unpacking the object yields these same four components.

    Raises
    ------
    ValueError
        If the input is not a version with two to four numeric components,
        optionally followed by a textual suffix
    """

    raw: str
    parts: tuple[int, int, int | None, int | None] = field(init=False)

    def __post_init__(self) -> None:
        """Validate the input and populate parts; raise ValueError if invalid."""
        raw = self.raw.strip() if isinstance(self.raw, str) else ""
        match = re.fullmatch(
            r"([0-9]+)\.([0-9]+)(?:[.-]([0-9]+))?(?:\.([0-9]+))?"
            r"(?:[.-][A-Za-z][A-Za-z0-9.-]*)?",
            raw,
        )
        if match is None:
            msg = f"Invalid MarkLogic version: {self.raw!r}"
            raise ValueError(msg)
        first, second, third, fourth = match.groups()
        object.__setattr__(self, "raw", raw)
        object.__setattr__(
            self,
            "parts",
            (
                int(first),
                int(second),
                int(third) if third is not None else None,
                int(fourth) if fourth is not None else None,
            ),
        )

    def __str__(self) -> str:
        """Return the complete version, including original separators and suffixes."""
        return self.raw

    def __iter__(self) -> Iterator[int | None]:
        """Yield all four numeric parts, using None for missing components."""
        return iter(self.parts)
