"""Interpret parsed evidence facts as resource states at a case cutoff."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from evidence_layer import Fact

@dataclass(frozen=True)
class ResourceState:
    resource_id: str
    system_id: str
    category: str
    present: bool | None
    exposed_identifiers: frozenset[str]
    attributable: bool
    active: bool | None
    restore_allowed: bool | None
    latest_fact: Fact | None
    evidence_fact: Fact | None

def system_for(resource_id: str, facts: Iterable[Fact] = ()) -> str:
    prefix = resource_id.rsplit("_", 1)[0]
    canonical = {"account":"account_service", "analytics":"analytics_platform", "backup":"backup_service", "export":"export_service", "search":"search_service", "audit_record":"security_service", "support":"support_platform", "data_flow":"integration_service", "tombstone":"identity_service", "marketing":"marketing_service", "cache":"cache_service", "object":"object_storage"}.get(prefix)
    if canonical: return canonical
    for fact in facts:
        if fact.system_id: return fact.system_id
    return {"account":"account_service", "analytics":"analytics_platform", "backup":"backup_service", "export":"export_service", "search":"search_service", "audit_record":"security_service", "support":"support_platform", "data_flow":"integration_service", "tombstone":"identity_service", "marketing":"marketing_service", "cache":"cache_service", "object":"object_storage"}.get(prefix, "unknown")

def category_for(resource_id: str, facts: Iterable[Fact] = ()) -> str:
    materialized = list(facts)
    for fact in materialized:
        c = fact.category.upper()
        if c in {"USER_PROFILE", "SECONDARY_IDENTIFIER", "SEARCH_INDEX_ENTRY", "CACHE_ENTRY", "SUPPORT_MESSAGE", "SUPPORT_ATTACHMENT", "ANALYTICS_PROFILE", "PRODUCT_TELEMETRY", "USER_EXPORT", "MARKETING_PROFILE", "EMAIL_DELIVERY_LOG", "SECURITY_AUDIT_LOG", "LEGAL_HOLD_RECORD", "BACKUP_ARCHIVE", "ACCOUNT_TOMBSTONE", "DATA_FLOW"}:
            return c
    # A diagnostic lookup event is not an analytics profile/telemetry record;
    # the event itself is a secondary identifier record governed by DELETE.
    for fact in materialized:
        event = str(fact.values.get("event", "")).casefold()
        if event in {"contact_lookup_completed", "contact_query_completed"}:
            return "SECONDARY_IDENTIFIER"
    prefix = resource_id.rsplit("_", 1)[0]
    return {"account":"USER_PROFILE", "analytics":"ANALYTICS_PROFILE", "backup":"BACKUP_ARCHIVE", "export":"USER_EXPORT", "search":"SEARCH_INDEX_ENTRY", "audit_record":"SECURITY_AUDIT_LOG", "support":"SUPPORT_MESSAGE", "data_flow":"DATA_FLOW", "tombstone":"ACCOUNT_TOMBSTONE", "marketing":"MARKETING_PROFILE", "cache":"CACHE_ENTRY"}.get(prefix, "SECONDARY_IDENTIFIER")

def _scalars(value: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    def visit(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items(): visit(v, f"{prefix}.{k}" if prefix else str(k))
        elif isinstance(obj, list):
            for v in obj: visit(v, prefix)
        else: result[prefix.casefold()] = obj
    visit(value); return result

def _bool_value(values: dict[str, Any], names: tuple[str, ...]) -> bool | None:
    for name in names:
        for key, value in values.items():
            if key.endswith(name):
                v = str(value).strip().casefold()
                if v in {"true", "1", "yes", "enabled", "active", "allowed"}: return True
                if v in {"false", "0", "no", "disabled", "blocked", "denied"}: return False
    return None

def resource_state(resource_id: str, facts: Iterable[Fact], identifiers: set[str], user_id: str | None, audit_at: str, linked_resources: set[str] | None = None) -> ResourceState:
    matching = [f for f in facts if f.resource_id == resource_id and f.timestamp <= audit_at and f.available_at <= audit_at]
    matching.sort(key=lambda f: (f.timestamp, f.available_at, f.evidence_id))
    latest = matching[-1] if matching else None
    state_fact: Fact | None = None; present: bool | None = None
    for fact in matching:
        values = _scalars(fact.values)
        status = " ".join(str(v).casefold() for k, v in values.items() if k.endswith("status") or k.endswith("status_code") or k.endswith("result") or k.endswith("rows") or k.endswith("http_status") or k.endswith("event"))
        if any(x in status for x in ("not_found", "not found", "absent", "no_match", "rows 0", "rows=0", "404")):
            present = False; state_fact = fact
        elif any(x in status for x in ("found", "identifiable", "active", "present", "rows 1", "rows=1", "hit", "read_completed", "200")):
            present = True; state_fact = fact
        elif fact.values.get("collection_name") or fact.values.get("collection") or fact.values.get("record_json"):
            # A row in a point-in-time SQL table is direct evidence of presence.
            present = True; state_fact = fact
        elif fact.resource_id and any(v is not None and str(v).strip().casefold() not in {"", "null", "none"} for k, v in values.items() if k.rsplit(".", 1)[-1] not in {"resource_id", "observed_at", "captured_at", "updated_at", "event_time", "timestamp", "exported_at", "event", "level", "severity", "service", "logger", "instance", "pod", "region", "trace_id", "lookup_key", "attempt"}):
            # Structured record/readback objects with substantive fields establish presence.
            present = True; state_fact = fact
        elif fact.raw and ("NOT_FOUND" in fact.raw or "not found" in fact.raw.casefold()):
            present = False; state_fact = fact
    chosen = state_fact or latest
    values = _scalars(chosen.values) if chosen else {}
    fields = {"email", "phone", "email_hash", "full_name", "name", "requester_name", "requester_email", "requester_phone", "owner_email", "customer_email", "customer_email", "display_name"}
    exposed: set[str] = set()
    for key, value in values.items():
        if key.rsplit(".", 1)[-1] in fields and value is not None and str(value).strip().casefold() not in {"", "null", "none"}:
            exposed.add(key.rsplit(".", 1)[-1])
        if key.rsplit(".", 1)[-1] in {"identifiers", "matched_identifiers", "matched_value", "matched_identifier", "detected_value", "correlation_key"} and value is not None:
            if any(alias.casefold() in str(value).casefold() for alias in identifiers if alias and alias.casefold() != (user_id or "").casefold()):
                exposed.add("identifiers")
    # Attributability is a proved identity path, not merely a populated profile:
    # any exact current/historical identifier match (including a known hash) or
    # an explicit edge to a subject-linked resource qualifies. This handles
    # de-identified records that retain user_id/customer_reference references.
    all_linkage = {str(value).strip().casefold() for value in values.values() if value is not None}
    attributable = bool({v.casefold() for v in identifiers} & all_linkage)
    related = {str(value).strip().casefold() for key, value in values.items()
               if "resource_id" in key.rsplit(".", 1)[-1] and key.rsplit(".", 1)[-1] != "resource_id" and value is not None}
    attributable = attributable or bool(related & {r.casefold() for r in (linked_resources or set())})
    active = _bool_value(values, ("enabled", "active", "is_active"))
    restore = _bool_value(values, ("restore_allowed", "restore_access", "can_restore"))
    status_text = " ".join(str(v).casefold() for k, v in values.items() if k.rsplit(".", 1)[-1] in {"status", "state", "result"})
    category = category_for(resource_id, matching)
    if category == "DATA_FLOW" and active is None:
        if any(x in status_text for x in ("active", "enabled", "running")): active = True
        elif any(x in status_text for x in ("disabled", "stopped", "inactive")): active = False
    if category == "BACKUP_ARCHIVE" and restore is None:
        if any(x in status_text for x in ("active", "allowed", "restorable")): restore = True
        elif any(x in status_text for x in ("blocked", "disabled", "not restorable")): restore = False
    evidence_fact = state_fact or (latest if present is not None else None)
    if category == "BACKUP_ARCHIVE" and restore is None:
        # Restore readbacks: eligible/deletion_block pairs or explicit authorization.
        for fact in matching:
            fv = _scalars(fact.values)
            elig = _bool_value(fv, ("eligible",)); blocked = _bool_value(fv, ("deletion_block",))
            decision = str(fv.get("decision", "")).strip().casefold()
            if elig is not None and blocked is not None: found = bool(elig and not blocked)
            elif decision in {"deny", "denied", "block", "blocked"}: found = False
            elif decision in {"allow", "allowed", "grant", "granted", "permit", "permitted"}: found = True
            else: continue
            restore = found; present = True if present is None else present
            evidence_fact = fact; chosen = fact
            break
    if category == "BACKUP_ARCHIVE" and restore and matching:
        # Prefer the earliest resource-specific readback establishing restore risk.
        evidence_fact = next((f for f in matching if f.resource_id == resource_id), evidence_fact)
    if evidence_fact is None and (active is not None or restore is not None): evidence_fact = latest
    return ResourceState(resource_id, system_for(resource_id, matching), category, present, frozenset(exposed), attributable, active, restore, latest, evidence_fact)
