"""Time-aware identity resolution across current snapshots and audit history."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

@dataclass(frozen=True)
class IdentityGraph:
    user_id: str | None
    identifiers: frozenset[str]
    emails: frozenset[str]
    strong_identifiers: frozenset[str]
    names: frozenset[str]
    ambiguous_users: frozenset[str]

def build_graph(request_email: str, audit_at: str, identities: list[dict[str, str]], audits: list[dict[str, str]]) -> IdentityGraph:
    requested = request_email.strip().casefold()
    name_owners: dict[str, set[str]] = {}
    for row in identities:
        for field in ("name", "full_name"):
            value = row.get(field, "").strip().casefold()
            if value: name_owners.setdefault(value, set()).add(row.get("user_id", ""))
    for row in audits:
        if "name" in row.get("field_name", "").casefold():
            for key in ("old_value", "new_value"):
                value = row.get(key, "").strip().casefold()
                if value: name_owners.setdefault(value, set()).add(row.get("user_id", ""))
    users: set[str] = set()
    for row in identities:
        stamp = row.get("updated_at") or row.get("snapshot_updated_at") or ""
        if row.get("email", "").strip().casefold() == requested and (not stamp or stamp <= audit_at):
            users.add(row["user_id"])
    for row in audits:
        if row.get("field_name", "").casefold() == "email" and row.get("event_time", "") <= audit_at:
            if requested in {row.get("old_value", "").strip().casefold(), row.get("new_value", "").strip().casefold()}:
                users.add(row["user_id"])
    if len(users) != 1:
        return IdentityGraph(None, frozenset({requested}), frozenset({requested}), frozenset({requested}), frozenset(), frozenset(users))
    uid = next(iter(users)); identifiers: set[str] = {uid}; emails: set[str] = {requested}; strong: set[str] = {uid}; names: set[str] = set()
    fields = ("name", "full_name", "email", "phone", "email_hash")
    for row in identities:
        stamp = row.get("updated_at") or row.get("snapshot_updated_at") or ""
        if row.get("user_id") == uid and (not stamp or stamp <= audit_at):
            for field in fields:
                value = row.get(field, "").strip()
                if value:
                    identifiers.add(value.casefold())
                    if field == "email": emails.add(value.casefold()); strong.add(value.casefold())
                    elif field in {"phone", "email_hash"}: strong.add(value.casefold())
                    elif field in {"name", "full_name"} and name_owners.get(value.casefold()) == {uid}: names.add(value.casefold())
    for row in audits:
        if row.get("user_id") == uid and row.get("event_time", "") <= audit_at:
            field_name = row.get("field_name", "").casefold()
            for field in ("old_value", "new_value"):
                value = row.get(field, "").strip()
                if value:
                    identifiers.add(value.casefold())
                    if "email" in field_name: emails.add(value.casefold()); strong.add(value.casefold())
                    elif "phone" in field_name or "hash" in field_name: strong.add(value.casefold())
                    elif "name" in field_name and name_owners.get(value.casefold()) == {uid}: names.add(value.casefold())
    strong.update(emails)
    hashes = {v for v in identifiers if len(v) == 64 and all(c in "0123456789abcdef" for c in v)}
    for email in emails:
        digest = hashlib.sha256(email.encode("utf-8")).hexdigest()
        if digest in hashes:
            identifiers.add(digest); strong.add(digest)
    return IdentityGraph(uid, frozenset(identifiers), frozenset(emails), frozenset(strong), frozenset(names), frozenset())

def matches_values(graph: IdentityGraph, values: dict[str, object], raw: str = "") -> bool:
    """Match typed identifiers exactly; names are only matched in identity fields."""
    flattened: dict[str, str] = {}
    def visit(obj: object, key: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items(): visit(v, str(k))
        elif isinstance(obj, list):
            for v in obj: visit(v, key)
        elif obj is not None:
            flattened[key.casefold()] = str(obj).strip().casefold()
    visit(values)
    if graph.strong_identifiers & set(flattened.values()): return True
    phones = {re.sub(r"\D", "", v) for v in graph.strong_identifiers if re.sub(r"\D", "", v)}
    for key, value in flattened.items():
        if key in {"phone", "requester_phone", "customer_phone", "owner_phone"} and re.sub(r"\D", "", value) in phones:
            return True
    if graph.names & {v for k, v in flattened.items() if k in {"name", "full_name", "requester_name", "customer_name", "display_name"}}: return True
    # Exact full email/hash in free text can bridge human-readable notes without substring name collisions.
    text = raw.casefold()
    if any(email in text for email in graph.emails): return True
    if any(re.search(r"(?<![0-9a-f])" + re.escape(v) + r"(?![0-9a-f])", text) for v in graph.strong_identifiers if len(v) == 64): return True
    if graph.user_id and re.search(r"\b" + re.escape(graph.user_id.casefold()) + r"\b", text): return True
    return False

def matches_fact(graph: IdentityGraph, fact: object) -> bool:
    tokens = getattr(fact, "scalar_tokens", set())
    if graph.strong_identifiers & tokens: return True
    keyed = getattr(fact, "keyed_values", {})
    if graph.names & (keyed.get("name", set()) | keyed.get("full_name", set()) | keyed.get("requester_name", set()) | keyed.get("customer_name", set()) | keyed.get("display_name", set())): return True
    raw = str(getattr(fact, "raw", "")).casefold()
    if any(email in raw for email in graph.emails): return True
    if graph.user_id and re.search(r"\b" + re.escape(graph.user_id.casefold()) + r"\b", raw): return True
    return False
