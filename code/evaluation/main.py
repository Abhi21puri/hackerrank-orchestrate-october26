"""Sample evaluator and output contract validator for the deletion audit agent."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("phase", "operation", "system_id", "resource_id", "state", "evidence_id", "step_no")
OPS = {
    "FINDING": {"REPORT_REMAINING_RECORD": "PRESENT", "REPORT_EXPOSED_PII": "PRESENT", "REPORT_ACTIVE_DATA_FLOW": "ACTIVE", "REPORT_RESTORE_RISK": "ACTIVE"},
    "REMEDIATION": {"DISABLE_DATA_FLOW": "DISABLED", "BLOCK_RESTORE": "BLOCKED", "DELETE_RECORD": "ABSENT", "REDACT_RECORD": "REDACTED", "ANONYMIZE_RECORD": "ANONYMIZED"},
    "VERIFICATION": {"VERIFY_RECORD_ABSENT": "ABSENT", "VERIFY_RECORD_PRESENT": "PRESENT", "VERIFY_RECORD_REDACTED": "REDACTED", "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED": "DISABLED", "VERIFY_RESTORE_BLOCKED": "BLOCKED"},
}

def load(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])

def parse_steps(row: dict[str, str], errors: list[str], label: str) -> list[dict[str, Any]]:
    try:
        steps = json.loads(row.get("steps_json", ""))
    except (ValueError, TypeError) as exc:
        errors.append(f"{label}/{row.get('case_id')}: invalid JSON: {exc}"); return []
    if not isinstance(steps, list):
        errors.append(f"{label}/{row.get('case_id')}: steps_json is not an array"); return []
    phases: list[int] = []
    order_key: list[tuple[int, int, str, str]] = []
    valid_status = row.get("deletion_status") in {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
    if not valid_status: errors.append(f"{label}/{row.get('case_id')}: illegal deletion_status")
    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict): errors.append(f"{label}/{row.get('case_id')}: step {i} is not an object"); continue
        if set(step) != {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}:
            errors.append(f"{label}/{row.get('case_id')}: step {i} has wrong fields")
        if step.get("step_no") != i: errors.append(f"{label}/{row.get('case_id')}: non-consecutive step_no at {i}")
        phase, op = step.get("phase"), step.get("operation")
        if phase not in OPS or op not in OPS.get(phase, {}): errors.append(f"{label}/{row.get('case_id')}: illegal phase/operation at {i}")
        else:
            phases.append(("FINDING", "REMEDIATION", "VERIFICATION").index(phase))
            order_key.append((("FINDING", "REMEDIATION", "VERIFICATION").index(phase), list(OPS[phase]).index(op), str(step.get("system_id", "")), str(step.get("resource_id", ""))))
            if step.get("state") != OPS[phase][op]: errors.append(f"{label}/{row.get('case_id')}: invalid state for step {i}")
        if phase == "FINDING" and not step.get("evidence_id"): errors.append(f"{label}/{row.get('case_id')}: finding lacks evidence id")
        if phase == "REMEDIATION" and step.get("evidence_id") != "": errors.append(f"{label}/{row.get('case_id')}: remediation evidence id must be empty")
        if phase == "VERIFICATION" and row.get("deletion_status") == "INCOMPLETE" and step.get("evidence_id") != "": errors.append(f"{label}/{row.get('case_id')}: future verification evidence id must be empty")
        if row.get("deletion_status") == "COMPLETE" and phase != "VERIFICATION": errors.append(f"{label}/{row.get('case_id')}: COMPLETE contains non-verification step")
        if row.get("deletion_status") == "COMPLETE" and not step.get("evidence_id"): errors.append(f"{label}/{row.get('case_id')}: COMPLETE verification lacks evidence id")
    if phases != sorted(phases): errors.append(f"{label}/{row.get('case_id')}: phase order violation")
    if order_key != sorted(order_key): errors.append(f"{label}/{row.get('case_id')}: operation/system/resource order violation")
    if row.get("deletion_status") == "NOT_APPLICABLE" and steps: errors.append(f"{label}/{row.get('case_id')}: NOT_APPLICABLE must use []")
    return steps

def evaluate(pred_path: Path, ref_path: Path, write_report: Path | None = None) -> dict[str, Any]:
    pred, phead = load(pred_path); ref, rhead = load(ref_path)
    errors: list[str] = []
    if phead != ["case_id", "deletion_status", "steps_json"]: errors.append(f"prediction header invalid: {phead}")
    if rhead != ["case_id", "deletion_status", "steps_json"]: errors.append(f"reference header invalid: {rhead}")
    pmap = {r["case_id"]: r for r in pred}; rmap = {r["case_id"]: r for r in ref}
    for label, rows in (("prediction", pred), ("reference", ref)):
        if len(rows) != len({r["case_id"] for r in rows}): errors.append(f"{label}: duplicate case_id")
        if [r["case_id"] for r in rows] != sorted(r["case_id"] for r in rows): errors.append(f"{label}: case_id sort order invalid")
        for row in rows: parse_steps(row, errors, label)
    common = sorted(pmap.keys() & rmap.keys())
    if set(pmap) != set(rmap): errors.append(f"case ids differ: missing={len(set(rmap)-set(pmap))} extra={len(set(pmap)-set(rmap))}")
    status_correct = sum(pmap[k]["deletion_status"] == rmap[k]["deletion_status"] for k in common)
    confusion = {a: {b: 0 for b in ("COMPLETE", "INCOMPLETE", "NOT_APPLICABLE")} for a in ("COMPLETE", "INCOMPLETE", "NOT_APPLICABLE")}
    for k in common: confusion[rmap[k]["deletion_status"]][pmap[k]["deletion_status"]] += 1
    ref_steps: set[tuple[Any, ...]] = set(); pred_steps: set[tuple[Any, ...]] = set(); diffs: list[dict[str, Any]] = []
    field_good = Counter(); field_total = Counter(); seq_good = 0; row_good = 0
    for k in common:
        ps = json.loads(pmap[k]["steps_json"]); rs = json.loads(rmap[k]["steps_json"])
        for s in ps: pred_steps.add((k, *(s.get(f) for f in FIELDS[:-1])))
        for s in rs: ref_steps.add((k, *(s.get(f) for f in FIELDS[:-1])))
        if ps == rs: seq_good += 1
        if ps == rs and pmap[k]["deletion_status"] == rmap[k]["deletion_status"]: row_good += 1
        if ps != rs or pmap[k]["deletion_status"] != rmap[k]["deletion_status"]:
            diffs.append({"case_id": k, "predicted_status": pmap[k]["deletion_status"], "reference_status": rmap[k]["deletion_status"], "predicted_step_count": len(ps), "reference_step_count": len(rs), "predicted_steps": ps, "reference_steps": rs})
        for i in range(max(len(ps), len(rs))):
            for field in FIELDS:
                field_total[field] += 1
                if i < len(ps) and i < len(rs) and ps[i].get(field) == rs[i].get(field): field_good[field] += 1
    tp = len(ref_steps & pred_steps); precision = tp / len(pred_steps) if pred_steps else float(not ref_steps); recall = tp / len(ref_steps) if ref_steps else float(not pred_steps)
    f1 = 2*precision*recall/(precision+recall) if precision+recall else 0.0
    result = {"cases": len(common), "status_accuracy": status_correct/len(common) if common else 0.0, "status_correct": status_correct, "confusion_matrix": confusion, "step_precision": precision, "step_recall": recall, "step_f1": f1, "step_tp": tp, "step_predicted": len(pred_steps), "step_reference": len(ref_steps), "field_accuracy": {f: field_good[f]/field_total[f] if field_total[f] else 0.0 for f in FIELDS}, "exact_sequence_rate": seq_good/len(common) if common else 0.0, "exact_sequence_correct": seq_good, "row_exact_rate": row_good/len(common) if common else 0.0, "schema_errors": errors, "case_diffs": diffs}
    if write_report:
        write_report.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Evaluation report", "", f"Compared `{pred_path}` with `{ref_path}`.", "", f"- Cases compared: {len(common)}", f"- Status accuracy: {status_correct}/{len(common)} = {result['status_accuracy']:.4f}", f"- Step precision / recall / F1: {precision:.4f} / {recall:.4f} / {f1:.4f} ({tp} TP, {len(pred_steps)} predicted, {len(ref_steps)} reference)", f"- Exact-sequence rate: {seq_good}/{len(common)} = {result['exact_sequence_rate']:.4f}", f"- Row exact rate: {row_good}/{len(common)} = {result['row_exact_rate']:.4f}", "", "## Confusion matrix (reference rows, predicted columns)", "", "| Reference \\ Predicted | COMPLETE | INCOMPLETE | NOT_APPLICABLE |", "|---|---:|---:|---:|"]
        for a, vals in confusion.items(): lines.append(f"| {a} | {vals['COMPLETE']} | {vals['INCOMPLETE']} | {vals['NOT_APPLICABLE']} |")
        lines += ["", "## Field accuracy", "", *[f"- {f}: {result['field_accuracy'][f]:.4f}" for f in FIELDS], "", f"## Schema validator\n\nErrors: {len(errors)}"]
        if errors: lines += ["", *[f"- {e}" for e in errors[:100]]]
        lines += ["", "## Per-case differences", ""]
        for diff in diffs:
            lines.append(f"- `{diff['case_id']}`: status {diff['predicted_status']} vs {diff['reference_status']}; steps {diff['predicted_step_count']} vs {diff['reference_step_count']}")
        write_report.write_text("\n".join(lines)+"\n", encoding="utf-8")
    return result

def validate_full_output(path: Path, dataset_dir: Path) -> dict[str, Any]:
    rows, header = load(path)
    errors: list[str] = []
    required = ["case_id", "deletion_status", "steps_json"]
    if header != required: errors.append(f"header invalid: {header}")
    requests = load(dataset_dir / "deletion_requests.csv")[0]
    expected = {r["case_id"] for r in requests}
    actual = [r["case_id"] for r in rows]
    if len(rows) != len(expected): errors.append(f"row count {len(rows)} != expected {len(expected)}")
    if len(actual) != len(set(actual)): errors.append("duplicate case_id")
    if set(actual) != expected: errors.append(f"case ids differ: missing={len(expected-set(actual))} extra={len(set(actual)-expected)}")
    if actual != sorted(actual): errors.append("case_id sort order invalid")
    for row in rows: parse_steps(row, errors, "output")
    available: dict[str, str] = {}
    for file in load(dataset_dir / "evidence_files.csv")[0]: available[file["file_id"]] = file["captured_at"]
    for activity in load(dataset_dir / "system_activity.csv")[0]: available[activity["activity_id"]] = activity["event_time"]
    for audit in load(dataset_dir / "user_audit_log.csv")[0]: available[audit["audit_id"]] = audit["event_time"]
    audit_at = {r["case_id"]: r["audit_at"] for r in requests}
    for row in rows:
        try: steps = json.loads(row["steps_json"])
        except (ValueError, TypeError): continue
        for step in steps:
            eid = step.get("evidence_id", "")
            if eid and eid not in available: errors.append(f"{row['case_id']}: unknown evidence id {eid}")
            elif eid and available[eid] > audit_at.get(row["case_id"], ""): errors.append(f"{row['case_id']}: evidence {eid} is after audit_at")
    return {"rows": len(rows), "status_distribution": dict(Counter(r["deletion_status"] for r in rows)), "schema_errors": errors}

def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("prediction", type=Path); ap.add_argument("reference", type=Path, nargs="?"); ap.add_argument("--dataset-dir", type=Path, default=ROOT / "dataset"); ap.add_argument("--validate-only", action="store_true"); ap.add_argument("--write-report", type=Path)
    a = ap.parse_args()
    if a.validate_only: result = validate_full_output(a.prediction, a.dataset_dir)
    elif a.reference: result = evaluate(a.prediction, a.reference, a.write_report)
    else: ap.error("reference is required unless --validate-only is set")
    print(json.dumps(result, indent=2))

if __name__ == "__main__": main()
