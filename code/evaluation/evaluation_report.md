# Evaluation report

## Public-sample metrics

Compared 32 public samples against `dataset/sample_output.csv`.

- Status accuracy: 32/32 = 1.00000
- Step precision / recall / F1: 1.00000 / 0.82383 / 0.90341 (159 TP; 159 predicted; 193 reference)
- Exact-sequence rate: 10/32 = 0.31250
- Field accuracy: phase 0.82383; operation 0.66321; system_id 0.61140; resource_id 0.61140; state 0.66321; evidence_id 0.82383; step_no 0.82383
- Sample schema errors: 0

## Confusion matrix (reference rows, predicted columns)

| Reference \ Predicted | COMPLETE | INCOMPLETE | NOT_APPLICABLE |
|---|---:|---:|---:|
| COMPLETE | 10 | 0 | 0 |
| INCOMPLETE | 0 | 22 | 0 |
| NOT_APPLICABLE | 0 | 0 | 0 |

## Full-run validation

- Rows: 518; validator errors: 0.
- Status mix: {'INCOMPLETE': 341, 'COMPLETE': 167, 'NOT_APPLICABLE': 10}.
- Deterministic reruns: identical SHA-256 `77970633D8D25A55983756B95715A85FA1D2BCB5C8FD18C449B780B0EB911849`.
- Non-NOT_APPLICABLE rows with zero steps (14): case_33, case_35, case_39, case_416, case_417, case_50, case_517, case_519, case_52, case_521, case_53, case_55, case_61, case_63.

## Custom cases

`python code/evaluation/custom_cases.py`: 5/5 passed.

1. `audit_at` cutoff excludes later evidence — PASS.
2. Historical email lookup — PASS.
3. Tombstone direct-identifier leak — PASS.
4. Claim without state evidence — PASS.
5. Non-English export request is not deletion — PASS.

## Failures found and improvements made

- Timestamp-prefixed JSON-lines were ignored; they are now parsed from the first `{` through the terminal `}`.
- Runtime-export key/value fields nested in escaped `message` strings were not exposed; parsing now extracts the nested fields, and trace grouping accepts `requestId`, `request_id`, and `correlation_id` as well as `trace_id`.
- Restore readbacks did not interpret `eligible`/`deletion_block` or explicit authorization decisions; the state interpreter now derives restorable state from these fields.
- JSON event timestamps can predate the evidence-file capture. Parsed facts now retain the manifest `captured_at` as availability time, preserving the required audit cutoff.

## Known limitations

- 14 authorized rows (case_33, case_35, case_39, case_416, case_417, case_50, case_517, case_519, case_52, case_521, case_53, case_55, case_61, case_63) are COMPLETE with empty steps because no grounded resource was found.
 - Remaining recall gaps include account absence checks without a subject link, de-identified analytics, and support/backup chains without a grounded link.
- OCR confidence is mixed; low-confidence text is excluded from facts. See `png_ocr_status.md` and `png_ocr_facts.md`.
- Time-window and activity-ID-neighbor joins remain rejected; identity resolution uses grounded identifiers, explicit references, and exact trace IDs.
