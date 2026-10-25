"""Deterministic deletion audit runner; paths are resolved from the repository root."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_layer import parse_manifest
from identity import build_graph
from planner import discover_resources, plan, serialize_steps
from policy import decide, load_rules
from state import resource_state

ROOT = Path(__file__).resolve().parents[1]
HEADER = ["case_id", "deletion_status", "steps_json"]
SORT_MODE = "plain_string"  # Switch to "numeric_suffix" only if the output contract changes.
PHASE_ORDER = {"FINDING": 0, "REMEDIATION": 1, "VERIFICATION": 2}
OPS = {
    "FINDING": ["REPORT_REMAINING_RECORD", "REPORT_EXPOSED_PII", "REPORT_ACTIVE_DATA_FLOW", "REPORT_RESTORE_RISK"],
    "REMEDIATION": ["DISABLE_DATA_FLOW", "BLOCK_RESTORE", "DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD"],
    "VERIFICATION": ["VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_RECORD_REDACTED", "VERIFY_RECORD_ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED", "VERIFY_RESTORE_BLOCKED"],
}

@dataclass(frozen=True)
class Case:
    case_id: str
    email: str
    requested_at: str
    audit_at: str
    request_text: str

@dataclass(frozen=True)
class Step:
    phase: str
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Required input file is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

def sort_key(case_id: str) -> tuple[str, ...]:
    if SORT_MODE == "plain_string": return (case_id,)
    if SORT_MODE == "numeric_suffix":
        match = re.fullmatch(r"([^0-9]*)([0-9]+)", case_id)
        if match: return (match.group(1), f"{int(match.group(2)):020d}")
    raise ValueError(f"Unsupported SORT_MODE={SORT_MODE!r}")

def positive_deletion(text: str) -> tuple[bool, str]:
    """Language-aware deletion intent; explicit non-deletion actions do not authorize erasure."""
    t = text.casefold().strip()
    other = r"\b(access|copy|export|download|correct|correction|update|replace|change|rectify|unsubscribe|opt\s*out|stop marketing|marketing only|marketing|promotional|do not sell)\b|\b(acceso|corregir|correcci[oó]n|exportar|descargar|cancelar suscripci[oó]n)\b|\b(acc[eè]s|corriger|correction|exporter|t[eé]l[eé]charger|d[eé]sabonner)\b|\b(acesso|corrigir|exportar|baixar|cancelar inscri[cç][aã]o)\b"
    delete = r"\b(delet(?:e|ed|ing|ion)|eras(?:e|ed|ing|ure)|remov(?:e|ed|ing|al)|close(?:d|ing)?|closure|wipe|destroy|right to be forgotten)\b|\b(eliminar|eliminaci[oó]n|borrar|suprimir|cerrar|cancelar)\b|\b(supprimer|suppression|effacer|cl[oô]turer|r[eé]silier)\b|\b(apagar|excluir|exclus[aã]o|eliminar)\b"
    cjk_delete = any(word in t for word in ("削除", "消去", "退会", "삭제", "지우", "탈퇴"))
    if re.search(r"\b(do not|don't|never|not asking to|not asking for|not a request to|without)\s+(?:a\s+)?(?:delet\w*|eras\w*|remov\w*|clos\w*|cancel\w*|destroy\w*|deactivat\w*)\b", t) or "삭제하지" in t or "削除しない" in t:
        return False, "negated deletion language"
    marketing_only = re.search(r"\b(remove|stop|unsubscribe|opt\s*out)\b.{0,60}\b(marketing|promotional)\b.{0,40}\bonly\b", t)
    explicit_account_deletion = re.search(r"\b(delet\w*|eras\w*|clos\w*|destroy\w*)\b.{0,60}\b(account|profile|personal data|my data)\b", t)
    if marketing_only and not explicit_account_deletion:
        return False, "marketing opt-out only"
    if re.search(other, t):
        # Explicit deletion can coexist with a minor request only if deletion is the clear action.
        if not re.search(delete, t) and not cjk_delete:
            return False, "non-deletion request language"
    if re.search(delete, t) or cjk_delete:
        return True, "positive deletion language"
    verification_of_erasure = r"\b(check|confirm|verify|inspect|audit|tell me whether)\b.{0,120}\b(account|profile|personal data)\b.{0,100}\b(gone|removed|erased|deleted|absent)\b|\b(account|profile)\b.{0,40}\b(is|was|has been)\b.{0,12}\bgone\b"
    if re.search(verification_of_erasure, t):
        return True, "request to verify an account deletion"
    return False, "no reliable deletion authorization phrase"

def classify_intent(text: str) -> tuple[bool, str, float]:
    authorized, reason = positive_deletion(text)
    if authorized:
        confidence = 0.88 if any(x in text for x in ("削除", "消去", "삭제", "지우")) else 0.95
    elif "negated" in reason or "non-deletion" in reason:
        confidence = 0.94
    else:
        confidence = 0.45
    return authorized, reason, confidence

def aliases_for(case: Case, identities: list[dict[str, str]], audits: list[dict[str, str]]) -> tuple[str | None, set[str]]:
    requested = case.email.strip().casefold()
    users: set[str] = set()
    for row in identities:
        if row.get("email", "").strip().casefold() == requested:
            users.add(row["user_id"])
    for row in audits:
        if row.get("field_name", "").casefold() == "email" and row.get("event_time", "") <= case.audit_at:
            for k in ("old_value", "new_value"):
                if row.get(k, "").strip().casefold() == requested:
                    users.add(row["user_id"])
    if len(users) != 1:
        return None, {requested}
    uid = next(iter(users))
    values = {requested, uid}
    for row in identities:
        if row.get("user_id") == uid:
            for k in ("name", "full_name", "email", "phone", "email_hash"):
                if row.get(k): values.add(row[k].strip().casefold())
    for row in audits:
        if row.get("user_id") == uid and row.get("event_time", "") <= case.audit_at:
            for k in ("old_value", "new_value"):
                if row.get(k): values.add(row[k].strip().casefold())
    # Include generated email digest only when it exactly agrees with the current snapshot.
    digest = hashlib.sha256(requested.encode()).hexdigest()
    if any(r.get("user_id") == uid and r.get("email_hash", "").casefold() == digest for r in identities):
        values.add(digest)
    return uid, values

def flatten_strings(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for v in value.values(): found |= flatten_strings(v)
    elif isinstance(value, list):
        for v in value: found |= flatten_strings(v)
    elif value is not None:
        found.add(str(value).strip().casefold())
    return found

def find_links(case: Case, uid: str | None, aliases: set[str], activities: list[dict[str, str]]) -> dict[str, tuple[str, str]]:
    resources: dict[str, tuple[str, str]] = {}
    terms = [x for x in aliases if x and len(x) > 3]
    for row in activities:
        if row.get("event_time", "") > case.audit_at:
            continue
        details = row.get("details", "").casefold()
        linked = bool(uid and re.search(r"\b" + re.escape(uid.casefold()) + r"\b", details)) or any(x in details for x in terms)
        if linked and row.get("resource_id"):
            res = row["resource_id"]
            system = row.get("target_system") or row.get("source_system") or "unknown"
            resources[res] = (system, row["activity_id"])
    return resources

def evidence_mentions(case: Case, aliases: set[str], evidence: list[dict[str, str]], dataset: Path) -> dict[str, list[tuple[str, str]]]:
    """Index file-level resource mentions grounded in identifiers, honoring capture time."""
    found: dict[str, list[tuple[str, str]]] = {}
    needles = [x for x in aliases if len(x) >= 5]
    for item in evidence:
        if item.get("captured_at", "") > case.audit_at:
            continue
        path = dataset / item["file_path"]
        if not path.is_file(): continue
        try: text = path.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        low = text.casefold()
        if not any(n in low for n in needles): continue
        for rid in set(re.findall(r"\b(?:account|analytics|backup|export|search|audit_record|support|data_flow|tombstone|marketing|cache|object)_\d+\b", low)):
            found.setdefault(rid, []).append((item["file_id"], text))
    return found

def build_steps(case: Case, uid: str | None, aliases: set[str], resources: dict[str, tuple[str, str]], evidence: list[dict[str, str]], dataset: Path) -> tuple[str, list[Step]]:
    mentioned = evidence_mentions(case, aliases, evidence, dataset)
    steps: list[Step] = []
    for rid, (system, activity_id) in resources.items():
        if rid in mentioned:
            # A participant-visible snapshot containing a subject's identifier is a remaining-data finding.
            ev_id = mentioned[rid][-1][0]
            steps.append(Step("FINDING", system, rid, "REPORT_REMAINING_RECORD", "PRESENT", ev_id))
            op = "DELETE_RECORD"; verify = "VERIFY_RECORD_ABSENT"; state = "ABSENT"
            if rid.startswith("data_flow_"): op="DISABLE_DATA_FLOW"; verify="VERIFY_DATA_FLOW_DISABLED"; state="DISABLED"
            elif rid.startswith("backup_"): op="BLOCK_RESTORE"; verify="VERIFY_RESTORE_BLOCKED"; state="BLOCKED"
            steps.append(Step("REMEDIATION", system, rid, op, state, ""))
            steps.append(Step("VERIFICATION", system, rid, verify, state, ""))
    if not steps:
        return "COMPLETE", []
    order = {op: i for phase in OPS.values() for i, op in enumerate(phase)}
    steps.sort(key=lambda s: (PHASE_ORDER[s.phase], order[s.operation], s.system_id, s.resource_id))
    return "INCOMPLETE", steps

def run(dataset: Path, output: Path, sample: bool = False, debug_case: str | None = None) -> int:
    requests = read_csv(dataset / ("sample_deletion_requests.csv" if sample else "deletion_requests.csv"))
    identities = read_csv(dataset / "user_identities.csv"); audits = read_csv(dataset / "user_audit_log.csv")
    activities = read_csv(dataset / "system_activity.csv"); evidence = read_csv(dataset / "evidence_files.csv")
    parsed = parse_manifest(dataset)
    rules = load_rules(dataset / "deletion_rules.csv")
    for warning in parsed.errors: logging.warning("%s", warning)
    rows: list[dict[str, str]] = []
    for raw in requests:
        case = Case(raw["case_id"], raw["email"], raw["requested_at"], raw["audit_at"], raw["request_text"])
        authorized, reason, confidence = classify_intent(case.request_text)
        graph = build_graph(case.email, case.audit_at, identities, audits)
        linked_resources = discover_resources(graph, parsed.facts, activities, case.audit_at, case.requested_at)
        classification_claim = any(
            row.get("event_type") == "CLASSIFY_REQUEST" and case.requested_at <= row.get("event_time", "") <= case.audit_at
            and row.get("resource_id") in linked_resources
            and "non-deletion" in row.get("details", "").casefold()
            for row in activities
        )
        if not authorized and classification_claim:
            reason = "non-deletion intent corroborated by linked intake classification"; confidence = min(0.99, confidence + 0.35)
        if not authorized:
            logging.warning("NOT_APPLICABLE case=%s confidence=%.2f reason=%s", case.case_id, confidence, reason)
            status, steps = "NOT_APPLICABLE", []
        else:
            resource_ids = linked_resources
            states = {rid: resource_state(rid, parsed.facts, set(graph.identifiers), graph.user_id, case.audit_at, resource_ids) for rid in resource_ids}
            decisions = {rid: decide(state, rules) for rid, state in states.items()}
            status, steps = plan(states, decisions)
        if debug_case == case.case_id:
            detail = {"case": case.case_id, "authorized": authorized, "reason": reason, "confidence": confidence, "status": status}
            if authorized: detail.update({"user_id": graph.user_id, "identifiers": sorted(graph.identifiers), "resources": {rid: {"state": states[rid].__dict__, "policy": decisions[rid].__dict__} for rid in sorted(states)}})
            detail["steps"] = serialize_steps(steps)
            print(json.dumps(detail, indent=2, default=str))
        encoded = serialize_steps(steps)
        rows.append({"case_id": case.case_id, "deletion_status": status, "steps_json": json.dumps(encoded, ensure_ascii=False, sort_keys=True, separators=(",", ":"))})
    rows.sort(key=lambda r: sort_key(r["case_id"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADER); writer.writeheader(); writer.writerows(rows)
    logging.info("Wrote %d rows to %s", len(rows), output)
    return len(rows)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=ROOT / "dataset")
    parser.add_argument("--output", type=Path, default=ROOT / "output.csv")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--debug-case")
    args = parser.parse_args(); logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try: run(args.dataset_dir.resolve(), args.output.resolve(), args.sample, args.debug_case)
    except (OSError, ValueError, KeyError) as exc:
        logging.error("Audit failed: %s", exc); sys.exit(2)

if __name__ == "__main__": main()
