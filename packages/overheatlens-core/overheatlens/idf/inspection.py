"""IDF inspection — an object-level parser for EnergyPlus input files.

The parser is deliberately small and explicit: it handles the standard IDF text
syntax (objects terminated by ';', '!' comments, fields separated by commas) and
macro lines are reported rather than silently executed. It exists to power readiness
checks and the IDF Passport; it does not attempt to validate against the EnergyPlus
schema (that is the engine's job at run time).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class IdfParseError(ValueError):
    """Raised when a file is not a parseable IDF at the structural level."""


@dataclass
class IdfObject:
    object_type: str
    fields: list[str]              # all fields after the type, order preserved
    index: int                     # ordinal among all objects (0-based)
    line: int                      # 1-based line where the object starts

    def f(self, i: int, default: str = "") -> str:
        return self.fields[i].strip() if i < len(self.fields) else default


@dataclass
class IdfModel:
    path: Path | None
    objects: list[IdfObject] = field(default_factory=list)
    has_macro_lines: bool = False
    sha256: str = ""

    def of_type(self, object_type: str) -> list[IdfObject]:
        t = object_type.strip().lower()
        return [o for o in self.objects if o.object_type.lower() == t]

    @property
    def types(self) -> set[str]:
        return {o.object_type.upper() for o in self.objects}

    def zone_names(self) -> list[str]:
        return [o.f(0) for o in self.of_type("Zone")]


def parse_idf(path: str | Path) -> IdfModel:
    """Parse an IDF file into objects, raising :class:`IdfParseError` on structural faults."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        raise IdfParseError(f"Cannot read file: {e}") from e

    from ..provenance.hashing import sha256_file

    model = IdfModel(path=path, sha256=sha256_file(path))

    # Strip '!' comments but keep line numbers.
    lines = text.splitlines()
    cleaned: list[tuple[int, str]] = []
    for i, ln in enumerate(lines, start=1):
        if ln.lstrip().startswith("##"):  # EP-Lucy / macro directives
            model.has_macro_lines = True
            continue
        code = ln.split("!", 1)[0]
        if code.strip():
            cleaned.append((i, code))

    blob = "\n".join(code for _, code in cleaned)

    import re

    chunks: list[tuple[str, list[str], int]] = []
    for m in re.finditer(r"[^;]*;", blob):
        seg = m.group(0)
        line = blob.count("\n", 0, m.start()) + 1
        parts = [p.strip() for p in seg.rstrip(";").split(",")]
        if not parts or not parts[0]:
            continue
        chunks.append((parts[0], parts[1:], line))

    if not chunks:
        raise IdfParseError(
            "No IDF objects found (objects must be comma-separated lists ending "
            "with a semicolon)."
        )

    model.objects = [
        IdfObject(object_type=ftype, fields=fields, index=i, line=line)
        for i, (ftype, fields, line) in enumerate(chunks)
    ]
    return model
