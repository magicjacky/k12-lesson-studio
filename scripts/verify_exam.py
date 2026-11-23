#!/usr/bin/env python3
"""
verify_exam.py — Deterministic Exam Score & Batch Grading Consistency Validator (k12-lesson-studio v5.0)

Prevents two classic AI teaching-prep hallucinations:
1. Exam section/item points not summing to 100, or missing step-by-step answers/rubrics.
2. Batch grading summary tables contradicting prose counts (e.g., table says 1 student missed a tag, heading says 2/4).

Usage:
  python verify_exam.py exam <exam_spec.json> [--target-total 100]
  python verify_exam.py grading <grading_records.json>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def verify_exam(spec_path: pathlib.Path, target_total: float = 100.0) -> dict:
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    sections = data.get("sections", [])
    errors = []
    section_totals = []
    question_count = 0

    for s_idx, sec in enumerate(sections, 1):
        sec_name = sec.get("title", f"Section {s_idx}")
        items = sec.get("items", [])
        sec_sum = 0.0
        for q_idx, item in enumerate(items, 1):
            question_count += 1
            pts = float(item.get("points", 0))
            sec_sum += pts
            if pts <= 0:
                errors.append(f"{sec_name} Q{q_idx}: non-positive points ({pts})")
            if not str(item.get("stem", "")).strip():
                errors.append(f"{sec_name} Q{q_idx}: empty stem")
            if str(item.get("answer", "")).strip() == "":
                errors.append(f"{sec_name} Q{q_idx}: empty answer")
        declared = sec.get("section_points")
        if declared is not None and abs(float(declared) - sec_sum) > 1e-6:
            errors.append(f"{sec_name}: declared section_points={declared} != sum(items)={sec_sum}")
        section_totals.append(round(sec_sum, 2))

    grand_total = round(sum(section_totals), 2)
    if abs(grand_total - target_total) > 1e-6:
        errors.append(f"Grand total {grand_total} != target {target_total}")
    if question_count == 0:
        errors.append("No exam questions found in sections")

    return {
        "passed": len(errors) == 0,
        "mode": "exam",
        "question_count": question_count,
        "section_totals": section_totals,
        "grand_total": grand_total,
        "errors": errors,
    }


def verify_grading(records_path: pathlib.Path) -> dict:
    data = json.loads(records_path.read_text(encoding="utf-8"))
    students = data.get("students", [])
    errors = []
    totals = []
    all_tags: list[str] = []

    if not students:
        errors.append("No student records found")

    for stu in students:
        name = stu.get("name", "<unnamed>")
        item_scores = stu.get("item_scores", {})
        calc_total = round(sum(float(v) for v in item_scores.values()), 2)
        declared_total = round(float(stu.get("total", calc_total)), 2)
        if abs(calc_total - declared_total) > 1e-6:
            errors.append(f"{name}: sum(item_scores)={calc_total} != declared total={declared_total}")
        totals.append(calc_total)

        error_tags = stu.get("error_tags", {})
        for tag, lost_items in error_tags.items():
            if not lost_items:
                errors.append(f"{name}: error_tag '{tag}' has empty item list")
            if tag not in all_tags:
                all_tags.append(tag)

    n = len(students)
    mean_score = round(sum(totals) / n, 2) if n else 0.0
    sorted_totals = sorted(totals)
    if n == 0:
        median_score = 0.0
    elif n % 2 == 1:
        median_score = sorted_totals[n // 2]
    else:
        median_score = round((sorted_totals[n // 2 - 1] + sorted_totals[n // 2]) / 2, 2)

    error_summary = {}
    for tag in all_tags:
        affected = [s.get("name", "") for s in students if tag in s.get("error_tags", {})]
        error_summary[tag] = {
            "count": len(affected),
            "ratio": f"{len(affected)}/{n}",
            "students": affected,
        }

    return {
        "passed": len(errors) == 0,
        "mode": "grading",
        "student_count": n,
        "mean": mean_score,
        "median": median_score,
        "error_summary": error_summary,
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    p_exam = sub.add_parser("exam", help="Validate exam JSON points sum and answers")
    p_exam.add_argument("json_path", type=pathlib.Path)
    p_exam.add_argument("--target-total", type=float, default=100.0)
    p_grad = sub.add_parser("grading", help="Validate student grading records and compute single-source error counts")
    p_grad.add_argument("json_path", type=pathlib.Path)
    args = ap.parse_args()

    res = verify_exam(args.json_path, args.target_total) if args.mode == "exam" else verify_grading(args.json_path)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
