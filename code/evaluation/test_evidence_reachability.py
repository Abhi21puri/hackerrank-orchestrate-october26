"""Check that each public sample citation resolves to evidence tied to its case."""
from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))
from evidence_layer import parse_manifest
from identity import build_graph, matches_values

def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

class CitationReachability(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        d = ROOT / "dataset"
        cls.requests = {r["case_id"]: r for r in csv_rows(d / "sample_deletion_requests.csv")}
        cls.outputs = csv_rows(d / "sample_output.csv")
        cls.identities = csv_rows(d / "user_identities.csv")
        cls.audits = csv_rows(d / "user_audit_log.csv")
        cls.activities = {r["activity_id"]: r for r in csv_rows(d / "system_activity.csv")}
        cls.audit_rows = {r["audit_id"]: r for r in cls.audits}
        cls.facts = parse_manifest(d).facts
        cls.facts_by_evidence: dict[str, list] = {}
        for fact in cls.facts: cls.facts_by_evidence.setdefault(fact.evidence_id, []).append(fact)

    def test_every_sample_citation_is_reachable_for_its_case(self) -> None:
        failures: list[str] = []
        for output in self.outputs:
            case = self.requests[output["case_id"]]
            graph = build_graph(case["email"], case["audit_at"], self.identities, self.audits)
            steps = json.loads(output["steps_json"])
            for step in steps:
                eid = step["evidence_id"]
                if not eid: continue
                if eid.startswith("evidence_"):
                    evidence_facts = self.facts_by_evidence.get(eid, [])
                    reachable = any(
                        f.timestamp <= case["audit_at"] and f.available_at <= case["audit_at"] and (
                            f.resource_id.casefold() == step["resource_id"].casefold()
                            or matches_values(graph, f.values, f.raw)
                        ) for f in evidence_facts
                    )
                    # A point-in-time SQL snapshot can prove an absence by a complete lookup
                    # against the relevant table even though the target row is not present.
                    if not reachable and step["operation"] == "VERIFY_RECORD_ABSENT" and any(f.available_at <= case["audit_at"] for f in evidence_facts):
                        prefix = step["resource_id"].rsplit("_", 1)[0]
                        table_terms = {
                            "account": ("customer_profiles",), "search": ("customer_search_documents",),
                            "analytics": ("customer_analytics",), "support": ("support_records",),
                            "export": ("customer_exports",), "backup": ("backup_restore_entries",),
                            "data_flow": ("connector_subscriptions",), "audit_record": ("security_audit_records",),
                            "tombstone": ("tombstone", "deleted_account"),
                        }.get(prefix, ())
                        collections = [str(f.values.get("collection_name", "")).casefold() for f in evidence_facts]
                        reachable = bool(table_terms and any(term in name for term in table_terms for name in collections))
                elif eid.startswith("activity_"):
                    row = self.activities.get(eid, {})
                    reachable = bool(row) and row.get("event_time", "") <= case["audit_at"] and (
                        row.get("resource_id") == step["resource_id"]
                        or bool(graph.user_id and graph.user_id.casefold() in row.get("details", "").casefold())
                        or any(alias in row.get("details", "").casefold() for alias in graph.identifiers if "@" in alias)
                    )
                elif eid.startswith("audit_"):
                    row = self.audit_rows.get(eid, {})
                    reachable = bool(row) and row.get("event_time", "") <= case["audit_at"] and bool(graph.user_id and row.get("user_id") == graph.user_id)
                else:
                    reachable = False
                if not reachable: failures.append(f"{case['case_id']} {step['resource_id']} <- {eid}")
        self.assertEqual(failures, [], "Unreachable or temporally invalid sample citations:\n" + "\n".join(failures))

if __name__ == "__main__": unittest.main()
