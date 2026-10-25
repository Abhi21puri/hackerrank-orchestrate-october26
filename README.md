# Ghost Data Still Exists — deletion audit

This deterministic Python program audits the 518 requests in `dataset/deletion_requests.csv`. It decides whether deletion was authorized, resolves current and historical identity, reconstructs state at `audit_at`, applies the supplied policy, and emits ordered findings, remediation, and verification steps in root `output.csv`.

## Architecture and data flow

`requests and policy CSVs -> identity graph -> cutoff-aware evidence facts -> resource state -> policy decision -> ordered planner -> output.csv`

- `code/main.py`: CLI, request intent, input/output contract, plain string sorting by `case_id` (`SORT_MODE`).
- `code/identity.py`: current and historical email, phone, name, hash, and user ID resolution.
- `code/evidence_layer.py`: manifest reader; SQL snapshots and `snapshot_scope`; JSON, JSONL, logs, TXT, PDFs, PNG OCR; evidence timestamps and parse warnings.
- `code/planner.py`: subject-grounded resource discovery, exact `trace_id` joins between lookup start/completion lines, identity-resource edges, and ordered plan construction. No time-window or activity-ID-neighbor joins are used.
- `code/state.py`: point-in-time present/absent, identifier exposure, active-flow and restore state.
- `code/policy.py`: applies `deletion_rules.csv`.
- `code/evaluation/main.py`: sample metrics and output/schema validator.
- `code/evaluation/custom_cases.py`: five participant-created behavior checks.

Evidence is eligible only when both its event/capture time and manifest `captured_at` are at or before `audit_at`. Exact trace IDs connect subject-keyed lookup or `subject_reference` lines to resource-bearing readbacks. Older account lookup traces predating the deletion request are excluded from account-state discovery. `LINK_RESOURCE_IDENTITY` alone does not establish resource state. Activity results are claims, not proof.

## Setup

Use Python 3.10 or later. Install evidence-reader dependencies:

```bash
python -m pip install pdfplumber pypdf pillow pytesseract
```

PNG OCR invokes Tesseract directly. The only optional environment variable is `TESSERACT_CMD`. If it is unset, the runner searches `PATH`. The documented Windows default is `C:\Program Files\Tesseract-OCR\tesseract.exe`; set `TESSERACT_CMD` to that executable when needed. If Tesseract is unavailable, each unparsed PNG is flagged and other evidence is still processed.

## Run and evaluate

From the repository root:

```bash
python code/main.py
python code/main.py --sample --output code/evaluation/sample_prediction.csv
python code/evaluation/main.py code/evaluation/sample_prediction.csv dataset/sample_output.csv --write-report code/evaluation/evaluation_report.md
python code/evaluation/main.py output.csv --validate-only --dataset-dir dataset
python code/evaluation/custom_cases.py
```

The runner writes exactly one plain-string-sorted row per request to root `output.csv`. `steps_json` is a JSON array with consecutive step numbers and the allowed phases, operations, and states. `NOT_APPLICABLE` rows have `[]`. Complete verification cites evidence; future verification in incomplete cases has an empty evidence ID.

## Design trade-offs and limitations

The implementation favors precision: identity is joined through exact identifiers, explicit resource references, and exact log trace IDs. It avoids temporal-neighbor inference even when it could add plausible resources. Consequently, de-identified analytics and other records without a participant-grounded identity link can remain unresolved. Some evidence contains no subject link beyond activity claims. PNG OCR confidence is mixed; low-confidence tokens are flagged and excluded from facts. No LLM or external service is used.
