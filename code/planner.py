"""Generate findings, ordered remediation, and complete end-state verification."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable

from evidence_layer import Fact, RESOURCE_RE
from identity import IdentityGraph, matches_fact
from policy import PolicyDecision
from state import ResourceState

@dataclass(frozen=True)
class PlannedStep:
    phase: str
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str

def _has_identifier(text: str, graph: IdentityGraph) -> bool:
    value = text.casefold()
    if graph.user_id and re.search(r"\b" + re.escape(graph.user_id.casefold()) + r"\b", value): return True
    for alias in graph.strong_identifiers:
        if "@" in alias and alias in value: return True
        if len(alias) == 64 and alias in value: return True
        if alias.startswith("+"):
            digits = re.sub(r"\D", "", alias)
            if digits and re.sub(r"\D", "", value).find(digits) >= 0: return True
    return False

def discover_resources(graph: IdentityGraph, facts: Iterable[Fact], activities: list[dict[str, str]], audit_at: str,
                       requested_at: str = "") -> set[str]:
    resources: set[str] = set()
    evidence_facts = [f for f in facts if f.timestamp <= audit_at and f.available_at <= audit_at]
    # Join start/completion records only through an exact trace identifier.
    # A subject-keyed lookup or subject_reference in one line grounds the
    # resource-bearing completion line in the same trace.
    trace_groups: dict[str, list[Fact]] = {}
    for fact in evidence_facts:
        trace = next((str(value) for key, values in fact.keyed_values.items() if key.endswith(("trace_id", "requestid", "request_id", "correlation_id")) for value in values), "")
        if trace: trace_groups.setdefault(trace, []).append(fact)
    for group in trace_groups.values():
        grounded = [fact for fact in group if matches_fact(graph, fact)]
        if grounded:
            for fact in group:
                if fact.resource_id:
                    # A pre-request account lookup can be a stale email alias
                    # collision and cannot establish post-request deletion state.
                    if fact.resource_id.startswith("account_") and requested_at and not any(
                        source.timestamp >= requested_at and any(k.endswith(("lookup_key", "email", "user_id", "subject_ref")) for k in source.keyed_values)
                        for source in grounded
                    ):
                        continue
                    resources.add(fact.resource_id)
    activity_edges: list[set[str]] = []
    link_events = {"SYNC_RECORD", "INDEX_RECORD", "CREATE_EXPORT", "LINK_RESOURCE_IDENTITY", "RESTORE_BACKUP"}
    for fact in evidence_facts:
        linked = matches_fact(graph, fact)
        stale_account_lookup = (fact.resource_id.startswith("account_") and requested_at
                                and fact.timestamp < requested_at
                                and any(key.endswith("lookup_key") for key in fact.keyed_values))
        if fact.resource_id and linked and not stale_account_lookup: resources.add(fact.resource_id)
        # Keep explicit foreign-key references between snapshots and records.
        references: set[str] = set()
        def collect_refs(value: object, key: str = "") -> None:
            if isinstance(value, dict):
                for k, v in value.items(): collect_refs(v, str(k).casefold())
            elif isinstance(value, list):
                for v in value: collect_refs(v, key)
            elif value is not None and "resource_id" in key:
                references.update(RESOURCE_RE.findall(str(value)))
        collect_refs(fact.values)
        edge = ({fact.resource_id} if fact.resource_id else set()) | references
        if len(edge) > 1: activity_edges.append(edge)
        if linked and not stale_account_lookup: resources.update(references)
    for row in activities:
        if row.get("event_time", "") > audit_at: continue
        details = row.get("details", "")
        resource_mentions = set(RESOURCE_RE.findall(details))
        row_resource = row.get("resource_id", "")
        edge = resource_mentions | ({row_resource} if RESOURCE_RE.fullmatch(row_resource) else set())
        if row.get("event_type", "").upper() in link_events and len(edge) > 1:
            activity_edges.append(edge)
        if _has_identifier(details, graph):
            resources.update(edge)
            if row_resource: resources.add(row_resource)
    # Close subject-linked record relations across sync, index, export, identity,
    # restore and replica references. Activity results remain claims, not state.
    added = True
    while added:
        added = False
        for edge in activity_edges:
            if edge & resources and not edge <= resources:
                resources.update(edge); added = True
    # LINK_RESOURCE_IDENTITY is ownership metadata, not evidence that the
    # target resource currently exists or has a state that needs verification.
    link_only = {row.get("resource_id", "") for row in activities
                 if row.get("event_time", "") <= audit_at and row.get("event_type", "").upper() == "LINK_RESOURCE_IDENTITY"
                 and _has_identifier(row.get("details", ""), graph)}
    state_ids = {f.resource_id for f in evidence_facts if f.resource_id}
    resources.difference_update(r for r in link_only if r not in state_ids)
    return resources

FINDING_STATES = {"REPORT_REMAINING_RECORD":"PRESENT", "REPORT_EXPOSED_PII":"PRESENT", "REPORT_ACTIVE_DATA_FLOW":"ACTIVE", "REPORT_RESTORE_RISK":"ACTIVE"}
REMEDIATION_STATES = {"DISABLE_DATA_FLOW":"DISABLED", "BLOCK_RESTORE":"BLOCKED", "DELETE_RECORD":"ABSENT", "REDACT_RECORD":"REDACTED", "ANONYMIZE_RECORD":"ANONYMIZED"}
VERIFICATION_STATES = {"VERIFY_RECORD_ABSENT":"ABSENT", "VERIFY_RECORD_PRESENT":"PRESENT", "VERIFY_RECORD_REDACTED":"REDACTED", "VERIFY_RECORD_ANONYMIZED":"ANONYMIZED", "VERIFY_DATA_FLOW_DISABLED":"DISABLED", "VERIFY_RESTORE_BLOCKED":"BLOCKED"}
PHASE_OPS = {"FINDING": tuple(FINDING_STATES), "REMEDIATION": tuple(REMEDIATION_STATES), "VERIFICATION": tuple(VERIFICATION_STATES)}

def plan(states: dict[str, ResourceState], decisions: dict[str, PolicyDecision]) -> tuple[str, list[PlannedStep]]:
    findings: list[PlannedStep] = []; remediations: list[PlannedStep] = []; verifications: list[PlannedStep] = []
    unresolved = False
    for rid, state in states.items():
        decision = decisions[rid]
        if decision.violation:
            ev = state.evidence_fact.evidence_id if state.evidence_fact else ""
            if not ev:
                unresolved = True
            elif decision.finding_operation:
                findings.append(PlannedStep("FINDING", state.system_id, rid, decision.finding_operation, FINDING_STATES[decision.finding_operation], ev))
            if decision.remediation_operation:
                op = decision.remediation_operation
                remediations.append(PlannedStep("REMEDIATION", state.system_id, rid, op, REMEDIATION_STATES[op], ""))
        # Each known resource receives the required future-state verification.
        verify = decision.verification_operation
        evidence = ""
        if state.evidence_fact:
            evidence = state.evidence_fact.evidence_id
        if verify == "VERIFY_RECORD_ABSENT" and state.present is not False: unresolved = True
        elif verify == "VERIFY_RECORD_REDACTED" and (state.present is not True or state.exposed_identifiers): unresolved = True
        elif verify == "VERIFY_RECORD_ANONYMIZED" and (state.present is not True or state.attributable or state.exposed_identifiers): unresolved = True
        elif verify == "VERIFY_RECORD_PRESENT" and state.present is not True: unresolved = True
        elif verify == "VERIFY_DATA_FLOW_DISABLED" and state.active is not False: unresolved = True
        elif verify == "VERIFY_RESTORE_BLOCKED" and state.restore_allowed is not False: unresolved = True
        if not evidence: unresolved = True
        verifications.append(PlannedStep("VERIFICATION", state.system_id, rid, verify, VERIFICATION_STATES[verify], evidence))
    incomplete = unresolved or bool(findings)
    if incomplete:
        # All checks follow planned future changes and have no evidence reference.
        verifications = [PlannedStep(s.phase, s.system_id, s.resource_id, s.operation, s.state, "") for s in verifications]
    steps = findings + remediations + verifications
    steps.sort(key=lambda s: (("FINDING", "REMEDIATION", "VERIFICATION").index(s.phase), PHASE_OPS[s.phase].index(s.operation), s.system_id, s.resource_id))
    return ("INCOMPLETE" if incomplete else "COMPLETE"), steps

def serialize_steps(steps: list[PlannedStep]) -> list[dict[str, object]]:
    return [{"step_no": i, **asdict(step)} for i, step in enumerate(steps, 1)]
