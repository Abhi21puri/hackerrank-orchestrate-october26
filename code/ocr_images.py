"""OCR all PNG evidence and write a confidence-aware extraction report."""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
from pathlib import Path

from evidence_layer import _ocr_tsv, _tesseract_command

ROOT = Path(__file__).resolve().parents[1]
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
RESOURCE_RE = re.compile(r"\b(?:account|analytics|backup|export|search|audit_record|support|data_flow|tombstone|marketing|cache|object)_\d+\b", re.I)
USER_RE = re.compile(r"\buser_\d+\b", re.I)

def run(dataset_dir: Path, report: Path, threshold: float = 60.0) -> int:
    exe = _tesseract_command()
    if not exe:
        raise RuntimeError("Tesseract is not set in TESSERACT_CMD or available on PATH")
    with (dataset_dir / "evidence_files.csv").open(encoding="utf-8-sig", newline="") as stream:
        pngs = [row for row in csv.DictReader(stream) if Path(row["file_path"]).suffix.casefold() == ".png"]
    version = subprocess.run([exe, "--version"], text=True, capture_output=True, check=False).stdout.splitlines()
    version_text = version[0] if version else "Tesseract version unavailable"
    sections = ["# PNG evidence OCR facts", "", f"Tesseract: `{version_text}`; low-confidence line threshold: {threshold:.0f}.", "", "Lines below the threshold are shown as uncertain and excluded from parsed facts. Text is preserved as recognized; apparent OCR errors are not corrected."]
    flagged: list[str] = []
    status_rows: list[tuple[str, str, int]] = []
    for row in pngs:
        path = dataset_dir / row["file_path"]
        lines, low, accepted = _ocr_tsv(exe, path, threshold)
        emails = sorted(set(EMAIL_RE.findall("\n".join(accepted))))
        resources = sorted(set(RESOURCE_RE.findall("\n".join(accepted))))
        users = sorted(set(USER_RE.findall("\n".join(accepted))))
        sections += ["", f"## {row['file_id']} — `{Path(row['file_path']).name}`", "", f"Captured: {row['captured_at']}", "", "### Extracted identifiers", ""]
        sections += [f"- Emails: {', '.join(emails) if emails else 'none confidently recognized'}", f"- Resource IDs: {', '.join(resources) if resources else 'none confidently recognized'}", f"- User IDs: {', '.join(users) if users else 'none confidently recognized'}"]
        fact_pattern = re.compile(r"(?:@|\b(?:account|analytics|backup|export|search|audit_record|support|data_flow|tombstone|marketing|cache|object)_\d+\b|\buser_\d+\b|active|disabled|blocked|restore|retention|expires|ready|deleted|retained|opt.?in|opt.?out|not found|found|status)", re.I)
        fact_lines = list(dict.fromkeys(line for line in accepted if fact_pattern.search(line)))
        sections += ["", "### High-confidence fact lines", ""]
        sections += [f"- {line}" for line in fact_lines] if fact_lines else ["- No high-confidence record or state line extracted."]
        marked_lines: list[str] = []
        for line in lines:
            marked_lines.append(line + ("  ⚠ LOW CONFIDENCE — uncertain words marked inline" if "⟦LOW " in line else ""))
        sections += ["", "### OCR text", "", "```text", *marked_lines, "```"]
        if low:
            flagged.append(row["file_id"])
            status_rows.append((row["file_id"], row["file_path"], len(low)))
            sections += ["", "### Uncertain lines", "", *[f"- {line}" for line in low]]
        else:
            status_rows.append((row["file_id"], row["file_path"], 0))
            sections += ["", "No OCR lines fell below the confidence threshold."]
    sections += ["", "## Summary", "", f"- PNG files processed: {len(pngs)}", f"- Files with low-confidence lines: {', '.join(flagged) if flagged else 'none'}"]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(sections) + "\n", encoding="utf-8")
    status = ["# PNG OCR status", "", f"Tesseract: `{version_text}`. Confidence threshold: {threshold:.0f}.", "", f"Detailed OCR text and facts: [{report.name}]({report.name})", "", "| Evidence ID | Image | Status |", "|---|---|---|"]
    for eid, name, low_count in status_rows:
        state = "OCR processed; no low-confidence lines" if low_count == 0 else f"OCR processed; {low_count} low-confidence lines flagged"
        status.append(f"| {eid} | `{Path(name).name}` | {state} |")
    report.with_name("png_ocr_status.md").write_text("\n".join(status) + "\n", encoding="utf-8")
    return len(pngs)

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset-dir", type=Path, default=ROOT / "dataset")
    ap.add_argument("--report", type=Path, default=ROOT / "code" / "evaluation" / "png_ocr_facts.md")
    ap.add_argument("--confidence-threshold", type=float, default=60.0)
    args = ap.parse_args()
    count = run(args.dataset_dir.resolve(), args.report.resolve(), args.confidence_threshold)
    print(f"OCR processed {count} PNGs; report: {args.report}")

if __name__ == "__main__": main()
