"""Canonical hashing, atomic durable writes and small shared helpers."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable


class VMEError(Exception):
    """Base error carrying a stable machine-readable code."""

    def __init__(self, code: str, detail: str = "", **data: Any):
        self.code = code
        self.detail = detail
        self.data = data
        super().__init__(f"{code}: {detail}" if detail else code)

    def to_dict(self) -> dict:
        return {"code": self.code, "detail": self.detail, "data": self.data}


class Blocked(VMEError):
    """A refusal: the requested operation must not proceed (never silently)."""


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_default)


def _default(o: Any):
    if isinstance(o, Path):
        return o.as_posix()
    if hasattr(o, "to_dict"):
        return o.to_dict()
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if isinstance(o, bytes):
        return {"__bytes_sha256__": sha256_bytes(o)}
    raise TypeError(f"not JSON serialisable: {type(o)!r}")


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str | os.PathLike, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def is_sha256(s: Any) -> bool:
    return isinstance(s, str) and re.fullmatch(r"[0-9a-f]{64}", s) is not None


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _fsync_dir(path: Path) -> None:
    # Directory fsync is unsupported on Windows; best effort elsewhere.
    if os.name == "nt":
        return
    try:
        fd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def atomic_write_bytes(path: str | os.PathLike, data: bytes) -> str:
    """temp -> flush -> fsync -> rename. Returns sha256 of written bytes."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
        _fsync_dir(p.parent)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return sha256_bytes(data)


def atomic_write_text(path: str | os.PathLike, text: str) -> str:
    return atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: str | os.PathLike, obj: Any, indent: int | None = 2) -> str:
    text = json.dumps(obj, indent=indent, sort_keys=True, ensure_ascii=False, default=_default) + "\n"
    return atomic_write_text(path, text)


def read_json(path: str | os.PathLike) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_jsonl(path: str | os.PathLike, record: Any) -> None:
    """Append-only log line, flushed and fsynced (used for raw event logs)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, ensure_ascii=False, default=_default) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_jsonl(path: str | os.PathLike) -> list:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def require_fields(obj: dict, fields: Iterable[str], code: str) -> None:
    missing = [k for k in fields if k not in obj or obj[k] in (None, "", [], {})]
    if missing:
        raise Blocked(code, f"missing/empty fields: {missing}", missing=missing)


# Words that, standing alone, are not an explanation of a visual relationship.
VAGUE_TERMS = (
    "beautiful", "vibrant", "dynamic", "professional", "polished", "rich", "nice",
    "appealing", "charming", "clean vector", "colourful", "colorful", "stunning",
    "harmonious", "kurzgesagt style", "kurzgesagt-like", "balanced", "detailed",
)

# Relationship vocabulary: an answer that names none of these and only vague terms is weak.
RELATION_TERMS = (
    "relative to", "relation", "between", "against", "versus", "while", "together",
    "changes", "overlap", "occlud", "silhouette", "separat", "contrast", "depends",
    "adapt", "when", "if ", "compared", "near", "far", "foreground", "background",
    "follows", "coordinat", "joins", "contact", "grip", "turns", "redraw", "replaced",
)


def is_vague_statement(text: str) -> bool:
    """True when a statement relies on standalone aesthetic adjectives with no visible relation."""
    t = (text or "").lower().strip()
    if len(t) < 25:
        return True
    has_vague = any(v in t for v in VAGUE_TERMS)
    has_relation = any(r in t for r in RELATION_TERMS)
    if not has_relation:
        return True
    # Mostly adjectives: strip vague terms and stop words, require substantive remainder.
    stripped = t
    for v in VAGUE_TERMS:
        stripped = stripped.replace(v, " ")
    words = [w for w in re.findall(r"[a-z]+", stripped) if len(w) > 3]
    return has_vague and len(words) < 6
