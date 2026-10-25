"""Rule application for category treatment and resource-state violations."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from state import ResourceState

@dataclass(frozen=True)
class PolicyDecision:
    category: str
    action: str
    violation: str | None
    verification_operation: str
    remediation_operation: str | None
    finding_operation: str | None

ACTION_MAP = {
    "DELETE": ("DELETE_RECORD", "VERIFY_RECORD_ABSENT", "REPORT_REMAINING_RECORD"),
    "REDACT": ("REDACT_RECORD", "VERIFY_RECORD_REDACTED", "REPORT_EXPOSED_PII"),
    "ANONYMIZE": ("ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED", "REPORT_EXPOSED_PII"),
    "RETAIN": (None, "VERIFY_RECORD_PRESENT", None),
}

def load_rules(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {row["data_category"]: row for row in csv.DictReader(stream)}

def decide(state: ResourceState, rules: dict[str, dict[str, str]]) -> PolicyDecision:
    category = state.category
    rule = rules.get(category)
    action = rule["required_action"] if rule else "DELETE"
    remediation, verify, finding = ACTION_MAP.get(action, ACTION_MAP["DELETE"])
    violation: str | None = None
    if category == "DATA_FLOW":
        action, verify, remediation, finding = "FLOW", "VERIFY_DATA_FLOW_DISABLED", "DISABLE_DATA_FLOW", "REPORT_ACTIVE_DATA_FLOW"
        violation = "active data flow" if state.active is True else None
    elif category == "BACKUP_ARCHIVE":
        action, verify, remediation, finding = "BACKUP", "VERIFY_RESTORE_BLOCKED", "BLOCK_RESTORE", "REPORT_RESTORE_RISK"
        violation = "restorable backup" if state.restore_allowed is True else None
    elif action == "DELETE":
        if state.present is True: violation = "record remains"
    elif action == "REDACT":
        if category == "SUPPORT_ATTACHMENT":
            # Delete only when evidence links the attachment's sole owner email
            # to this subject; multi-owner attachments remain under policy.
            sole_owner = bool(state.latest_fact and state.latest_fact.values.get("owner_email"))
            violation = "record remains" if state.present is True and state.attributable and sole_owner else None
            if violation:
                action, remediation, verify, finding = "DELETE", "DELETE_RECORD", "VERIFY_RECORD_ABSENT", "REPORT_REMAINING_RECORD"
        elif state.present is True and state.exposed_identifiers:
            violation = "identifiers exposed"
    elif action == "ANONYMIZE":
        if state.present is True and (state.attributable or state.exposed_identifiers): violation = "record still attributable"
    elif action == "RETAIN":
        # Active legal holds and in-window security records are retained; expired
        # records require deletion only when evidence provides their expiry condition.
        if state.present is True: violation = None
    return PolicyDecision(category, action, violation, verify, remediation, finding)
