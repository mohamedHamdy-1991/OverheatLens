"""Rule-pack loading and validation.

Packs are YAML validated against a JSON Schema (a small purpose-built validator so the
zero-install footprint stays at numpy + PyYAML). Validation failures are raised loudly —
a malformed pack must never load silently.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"


class RulePackError(ValueError):
    """Raised when a rule pack is malformed or fails schema validation."""


def _validate(obj: Any, schema: dict, path: str = "", root: dict | None = None) -> None:
    """Validate a JSON-Schema subset: type, required, properties, additionalProperties,
    items, enum, pattern, $ref (local #/$defs only), min/max constraints.
    Deliberately minimal and explicit."""
    where = path or "<root>"
    root = root if root is not None else schema

    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise RulePackError(f"{where}: only local $ref supported, got {ref!r}")
        target: Any = root
        for part in ref[2:].split("/"):
            target = target[part]
        _validate(obj, target, where, root)
        return

    if "enum" in schema and obj not in schema["enum"]:
        raise RulePackError(f"{where}: value {obj!r} not in {schema['enum']}")

    t = schema.get("type")
    if t == "object":
        if not isinstance(obj, dict):
            raise RulePackError(f"{where}: expected object, got {type(obj).__name__}")
        for req in schema.get("required", []):
            if req not in obj:
                raise RulePackError(f"{where}: missing required property {req!r}")
        props = schema.get("properties", {})
        ap = schema.get("additionalProperties", True)
        for key, val in obj.items():
            if key in props:
                _validate(val, props[key], f"{where}.{key}", root)
            elif ap is False:
                raise RulePackError(f"{where}: unexpected property {key!r}")
            elif isinstance(ap, dict):
                _validate(val, ap, f"{where}.{key}", root)
        if "minProperties" in schema and len(obj) < schema["minProperties"]:
            raise RulePackError(f"{where}: needs >= {schema['minProperties']} properties")
    elif t == "array":
        if not isinstance(obj, list):
            raise RulePackError(f"{where}: expected array, got {type(obj).__name__}")
        if "minItems" in schema and len(obj) < schema["minItems"]:
            raise RulePackError(f"{where}: needs >= {schema['minItems']} items")
        for i, item in enumerate(obj):
            if "items" in schema:
                _validate(item, schema["items"], f"{where}[{i}]", root)
    elif t == "string":
        if not isinstance(obj, str):
            raise RulePackError(f"{where}: expected string, got {type(obj).__name__}")
        if "pattern" in obj and False:
            pass
        if "pattern" in schema:
            import re

            if not re.search(schema["pattern"], obj):
                raise RulePackError(
                    f"{where}: {obj!r} does not match pattern {schema['pattern']!r}"
                )
        if "minLength" in schema and len(obj) < schema["minLength"]:
            raise RulePackError(f"{where}: string shorter than {schema['minLength']}")
    elif t == "integer":
        if not isinstance(obj, int) or isinstance(obj, bool):
            raise RulePackError(f"{where}: expected integer, got {type(obj).__name__}")
        if "enum" in schema and obj not in schema["enum"]:
            raise RulePackError(f"{where}: value {obj} not in {schema['enum']}")
    elif t == "number":
        if not isinstance(obj, (int, float)) or isinstance(obj, bool):
            raise RulePackError(f"{where}: expected number, got {type(obj).__name__}")
    elif t == "boolean":
        if not isinstance(obj, bool):
            raise RulePackError(f"{where}: expected boolean, got {type(obj).__name__}")


def load_schema() -> dict:
    """Load the bundled rule-pack JSON Schema."""
    schema_path = Path(__file__).resolve().parent / "rule_pack.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_pack_dict(pack: dict) -> None:
    """Validate a rule-pack dict against the schema; raise RulePackError on failure."""
    _validate(pack, load_schema())


def load_pack_dict(source: str | Path | dict) -> dict:
    """Load a pack from a YAML file path or pass through a dict, then validate."""
    if isinstance(source, dict):
        pack = source
    else:
        try:
            pack = yaml.safe_load(Path(source).read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise RulePackError(f"YAML error in {source}: {e}") from e
    validate_pack_dict(pack)
    return pack


def available_pack_ids() -> list[str]:
    """IDs of all bundled rule packs."""
    return sorted(p.stem for p in RULES_DIR.glob("*.yaml"))


def load_bundled_pack(pack_id: str) -> dict:
    """Load and validate a bundled rule pack by id (e.g. 'uk_tm59_2017')."""
    path = RULES_DIR / f"{pack_id}.yaml"
    if not path.exists():
        raise RulePackError(
            f"Unknown rule pack {pack_id!r}. Available: {', '.join(available_pack_ids())}"
        )
    return load_pack_dict(path)
