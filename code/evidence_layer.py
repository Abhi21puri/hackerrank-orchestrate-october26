"""Deterministic, cutoff-aware readers for supplied deletion audit evidence."""
from __future__ import annotations

import json
import io
import os
import re
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

@dataclass(frozen=True)
class EvidenceFile:
    evidence_id: str
    path: Path
    captured_at: str

@dataclass
class Fact:
    evidence_id: str
    timestamp: str
    available_at: str
    system_id: str = ""
    resource_id: str = ""
    category: str = ""
    values: dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    scalar_tokens: set[str] = field(init=False)
    keyed_values: dict[str, set[str]] = field(init=False)

    def __post_init__(self) -> None:
        tokens: set[str] = set(); keyed: dict[str, set[str]] = {}
        def walk(obj: Any, key: str = "") -> None:
            if isinstance(obj, dict):
                for k, v in obj.items(): walk(v, str(k).casefold())
            elif isinstance(obj, list):
                for v in obj: walk(v, key)
            elif obj is not None:
                token = str(obj).strip().casefold()
                if token: tokens.add(token); keyed.setdefault(key, set()).add(token)
        walk(self.values)
        emails = re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", self.raw, re.I)
        tokens.update(x.casefold() for x in emails)
        self.scalar_tokens = tokens; self.keyed_values = keyed

    def tokens(self) -> set[str]:
        result = {self.resource_id.casefold()} if self.resource_id else set()
        result |= self.scalar_tokens
        return result

@dataclass
class ParseResult:
    facts: list[Fact]
    errors: list[str]
    png_flags: list[str]

RESOURCE_RE = re.compile(r"\b(?:account|analytics|backup|export|search|audit_record|support|data_flow|tombstone|marketing|cache|object)_\d+\b", re.I)
TIMESTAMP_RE = re.compile(r"\b\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z\b")
FIELD_RE = re.compile(r'([A-Za-z_][\w.-]*)\s*[:=]\s*("(?:[^"\\]|\\.)*"|\S+)')

def _tesseract_command() -> str | None:
    configured = os.environ.get("TESSERACT_CMD", "").strip()
    if configured:
        return configured if Path(configured).is_file() else None
    return shutil.which("tesseract")

def _ocr_tsv(executable: str, path: Path, threshold: float = 60.0) -> tuple[list[str], list[str], list[str]]:
    # Sparse-text mode works better for application screenshots and emits one word per TSV row.
    proc = subprocess.run([executable, str(path), "stdout", "--psm", "11", "tsv"], text=True, capture_output=True, check=False)
    if proc.returncode: raise RuntimeError(proc.stderr.strip() or "tesseract failed")
    import csv
    import io as text_io
    grouped: dict[tuple[str, str, str, str], list[tuple[float, str]]] = {}
    for row in csv.DictReader(text_io.StringIO(proc.stdout), delimiter="\t"):
        word = row.get("text", "").strip()
        try: confidence = float(row.get("conf", "-1"))
        except ValueError: confidence = -1
        if word and confidence >= 0:
            key = (row.get("page_num", "1"), row.get("block_num", "0"), row.get("par_num", "0"), row.get("line_num", "0"))
            grouped.setdefault(key, []).append((confidence, word))
    lines: list[str] = []; low: list[str] = []; accepted: list[str] = []
    for words in grouped.values():
        text = " ".join(word if conf >= threshold else f"⟦LOW {conf:.0f}: {word}⟧" for conf, word in words)
        certain = " ".join(word for conf, word in words if conf >= threshold)
        minimum = min(conf for conf, _ in words)
        average = sum(conf for conf, _ in words) / len(words)
        lines.append(f"{text} [line confidence min={minimum:.1f}, avg={average:.1f}]")
        if minimum < threshold: low.append(f"{text} [line confidence min={minimum:.1f}, avg={average:.1f}]")
        if certain: accepted.append(certain)
    return lines, low, accepted

def _fact(eid: str, ts: str, value: dict[str, Any], raw: str = "", available_at: str = "") -> Fact:
    rid = str(value.get("resource_id") or "")
    system = str(value.get("system_id") or value.get("data_store") or value.get("origin_system") or value.get("service") or "")
    cat = str(value.get("data_category") or value.get("category") or value.get("collection") or value.get("collection_name") or "")
    return Fact(eid, ts, available_at or ts, system, rid, cat, value, raw)

def _walk_json(obj: Any, eid: str, fallback_ts: str, out: list[Fact], parent: dict[str, Any] | None = None, available_at: str = "") -> None:
    if isinstance(obj, dict):
        carry = {k: v for k, v in (parent or {}).items() if k in {"captured_at", "observed_at", "data_store", "origin_system", "system_id", "service", "collection", "collection_name", "resource_id", "user_id", "customer_reference"}}
        context = {**carry, **obj}
        ts = str(obj.get("captured_at") or obj.get("observed_at") or obj.get("updated_at") or obj.get("event_time") or fallback_ts)
        if any(k in context for k in ("resource_id", "customer_reference", "email", "requester_email", "owner_email")):
            out.append(_fact(eid, ts, context, json.dumps(obj, ensure_ascii=False), available_at or fallback_ts))
        for v in obj.values(): _walk_json(v, eid, ts, out, context, available_at or fallback_ts)
    elif isinstance(obj, list):
        for v in obj: _walk_json(v, eid, fallback_ts, out, parent, available_at or fallback_ts)

def _parse_lines(eid: str, text: str, captured: str) -> list[Fact]:
    facts: list[Fact] = []
    for line in text.splitlines():
        if not line.strip(): continue
        mt = TIMESTAMP_RE.search(line); ts = mt.group(0) if mt else captured
        brace = line.find("{")
        if brace >= 0 and line.rstrip().endswith("}"):
            # JSON-lines records, with or without a leading timestamp prefix.
            try:
                obj = json.loads(line[brace:])
                if isinstance(obj, dict): facts.append(_fact(eid, ts, obj, line, captured)); continue
            except json.JSONDecodeError: pass
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5 and RESOURCE_RE.fullmatch(parts[2]):
                facts.append(_fact(eid, ts, {"system_id": parts[1], "resource_id": parts[2], "category": parts[3], "status": parts[4], "identifiers": " ".join(parts[5:])}, line)); continue
        values = {k: v.strip('"') for k, v in FIELD_RE.findall(line)}
        message = values.get("message")
        if message and "=" in message:
            # Runtime exports nest key=value pairs in escaped message strings.
            for k, v in FIELD_RE.findall(message.replace('\\"', '"')):
                values.setdefault(k, v.strip('"'))
        rid = RESOURCE_RE.search(line)
        if rid: values.setdefault("resource_id", rid.group(0))
        if values: facts.append(_fact(eid, ts, values, line, captured))
    return facts

def _single_owner_attachment_fact(eid: str, captured: str, text: str, path: Path) -> list[Fact]:
    """Link a uniquely identified support attachment to its sole email owner."""
    if "attachment" not in path.name.casefold(): return []
    resource_ids = set(RESOURCE_RE.findall(text))
    emails = set(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I))
    if len(resource_ids) != 1 or len(emails) != 1: return []
    rid = next(iter(resource_ids))
    return [_fact(eid, captured, {"resource_id": rid, "category": "SUPPORT_ATTACHMENT", "owner_email": next(iter(emails))}, text, captured)]

def _parse_sql(item: EvidenceFile) -> list[Fact]:
    sql = item.path.read_text(encoding="utf-8", errors="replace")
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(sql)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        scope: dict[str, str] = {}
        if "snapshot_scope" in tables:
            for origin, stamp in conn.execute("SELECT origin_system,captured_at FROM snapshot_scope"):
                scope[str(origin)] = str(stamp)
        facts: list[Fact] = []
        for table in tables:
            if table == "snapshot_scope": continue
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
            for tup in conn.execute(f'SELECT * FROM "{table}"'):
                row = dict(zip(cols, tup))
                if "record_json" in row and row["record_json"]:
                    try:
                        embedded = json.loads(row["record_json"])
                        if isinstance(embedded, dict): row = {**row, **embedded}
                    except (ValueError, TypeError): pass
                origin = str(row.get("origin_system") or row.get("system_id") or "")
                # Snapshot scope is the availability time of a SQL observation.
                ts = scope.get(origin, item.captured_at)
                row.setdefault("collection_name", table)
                row.setdefault("origin_system", origin)
                facts.append(_fact(item.evidence_id, ts, row, available_at=item.captured_at))
        return facts
    finally:
        conn.close()

def parse_file(item: EvidenceFile) -> tuple[list[Fact], str | None]:
    suffix = item.path.suffix.casefold()
    if suffix == ".sql": return _parse_sql(item), None
    if suffix in (".json", ".jsonl"):
        raw = item.path.read_text(encoding="utf-8", errors="replace")
        facts: list[Fact] = []
        if suffix == ".jsonl": return _parse_lines(item.evidence_id, raw, item.captured_at), None
        try: _walk_json(json.loads(raw), item.evidence_id, item.captured_at, facts, available_at=item.captured_at)
        except json.JSONDecodeError: return _parse_lines(item.evidence_id, raw, item.captured_at), f"{item.evidence_id}: malformed JSON; parsed as text"
        return facts, None
    if suffix in (".log", ".txt"): return _parse_lines(item.evidence_id, item.path.read_text(encoding="utf-8", errors="replace"), item.captured_at), None
    if suffix == ".pdf":
        import pdfplumber
        with pdfplumber.open(item.path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            if not text.strip():
                exe = _tesseract_command()
                if not exe: return [], f"{item.evidence_id}: PDF has no text layer and tesseract executable is unavailable for OCR"
                pages: list[str] = []
                for page in pdf.pages:
                    image = page.to_image(resolution=240).original
                    buffer = io.BytesIO(); image.save(buffer, format="PNG")
                    proc = subprocess.run([exe, "stdin", "stdout"], input=buffer.getvalue(), capture_output=True, check=False)
                    if proc.returncode: return [], f"{item.evidence_id}: PDF OCR failed: {proc.stderr.decode(errors='replace').strip()}"
                    pages.append(proc.stdout.decode("utf-8", errors="replace"))
                text = "\n".join(pages)
        facts = _parse_lines(item.evidence_id, text, item.captured_at)
        facts.extend(_single_owner_attachment_fact(item.evidence_id, item.captured_at, text, item.path))
        return facts, None
    if suffix == ".png":
        exe = _tesseract_command()
        if not exe: return [], f"{item.evidence_id}: PNG not OCR-parsed because tesseract executable is unavailable"
        try: lines, low, accepted = _ocr_tsv(exe, item.path)
        except RuntimeError as exc: return [], f"{item.evidence_id}: tesseract OCR failed: {exc}"
        warning = f"{item.evidence_id}: {len(low)} low-confidence OCR lines (see evaluation/png_ocr_facts.md)" if low else None
        accepted_text = "\n".join(accepted)
        # OCR can separate a known resource prefix from its numeric suffix. Join
        # only that exact high-confidence token pattern; never repair low tokens.
        accepted_text = re.sub(r"\b(account|analytics|backup|export|search|audit_record|support|data_flow|tombstone|marketing|cache|object)\s+(\d+)\b", r"\1_\2", accepted_text, flags=re.I)
        return _parse_lines(item.evidence_id, accepted_text, item.captured_at), warning
    return [], f"{item.evidence_id}: unsupported evidence type {suffix}"

def parse_manifest(dataset_dir: Path) -> ParseResult:
    import csv
    manifest_path = dataset_dir / "evidence_files.csv"
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    facts: list[Fact] = []; errors: list[str] = []; flags: list[str] = []
    for row in manifest:
        item = EvidenceFile(row["file_id"], dataset_dir / row["file_path"], row["captured_at"])
        try: parsed, warning = parse_file(item)
        except Exception as exc:
            parsed, warning = [], f"{item.evidence_id}: parser error: {type(exc).__name__}: {exc}"
        facts.extend(parsed)
        if warning:
            errors.append(warning)
            if item.path.suffix.casefold() == ".png": flags.append(warning)
    return ParseResult(facts, errors, flags)

def for_case(facts: Iterable[Fact], identifiers: set[str], audit_at: str) -> list[Fact]:
    normalized = {x.strip().casefold() for x in identifiers if x and len(x.strip()) >= 3}
    return [fact for fact in facts if fact.timestamp <= audit_at and fact.available_at <= audit_at and bool(normalized & fact.tokens())]
