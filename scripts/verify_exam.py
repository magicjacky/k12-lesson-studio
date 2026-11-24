#!/usr/bin/env python3
"""
verify_exam.py — Deterministic Exam Score, Single-Source Paper Exporter & Batch Grading Validator (k12-lesson-studio v5.1)

Prevents classic AI teaching-prep hallucinations:
1. Exam section/item points not summing to target (default 100), or missing step-by-step answers/rubrics.
2. Discrepancies between student paper and teacher key (optional single-source Markdown export for both).
3. Batch grading summary tables contradicting prose counts (single-source aggregation + optional summary Markdown).

Usage:
  python verify_exam.py exam <exam_spec.json> [--target-total 100] [--export-student-md <s.md>] [--export-teacher-md <t.md>]
  python verify_exam.py grading <grading_records.json> [--export-summary-md <g.md>]
"""
from __future__ import annotations

import argparse
import json
import pathlib


def verify_exam(spec_path: pathlib.Path, target_total: float = 100.0) -> tuple[dict, dict]:
    data = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    sections = data.get("sections", [])
    errors = []
    section_totals = []
    question_count = 0

    for s_idx, sec in enumerate(sections, 1):
        sec_name = sec.get("title", f"第{s_idx}大题")
        items = sec.get("items", [])
        sec_sum = 0.0
        for q_idx, item in enumerate(items, 1):
            question_count += 1
            pts = float(item.get("points", 0))
            sec_sum += pts
            if pts <= 0:
                errors.append(f"{sec_name} 第{q_idx}题: 分值必须大于 0 ({pts})")
            if not str(item.get("stem", "")).strip():
                errors.append(f"{sec_name} 第{q_idx}题: 题干为空")
            if str(item.get("answer", "")).strip() == "":
                errors.append(f"{sec_name} 第{q_idx}题: 参考答案为空")
            opts = item.get("options")
            if opts is not None and (not isinstance(opts, list) or len(opts) < 2):
                errors.append(f"{sec_name} 第{q_idx}题: options 至少需要 2 个选项")
        declared = sec.get("section_points")
        if declared is not None and abs(float(declared) - sec_sum) > 1e-6:
            errors.append(f"{sec_name}: 声明分值 {declared} != 小题分值之和 {sec_sum}")
        section_totals.append(round(sec_sum, 2))

    grand_total = round(sum(section_totals), 2)
    if abs(grand_total - target_total) > 1e-6:
        errors.append(f"全卷总分 {grand_total} != 目标总分 {target_total}")
    if question_count == 0:
        errors.append("sections 中未找到任何题目")

    report = {
        "passed": len(errors) == 0,
        "mode": "exam",
        "title": data.get("title", ""),
        "question_count": question_count,
        "section_totals": section_totals,
        "grand_total": grand_total,
        "errors": errors,
    }
    return report, data


def render_exam_markdown(data: dict, teacher: bool = False) -> str:
    title = data.get("title", "单元随堂测试卷")
    suffix = "（教师解析与评分标准卷）" if teacher else "（学生作答卷）"
    duration = data.get("duration_min", 40)
    total = data.get("target_total", 100)
    subtitle = data.get("subtitle", f"考试时间：{duration} 分钟    满分：{total} 分")
    notice = data.get("notice", "")

    lines = [f"# {title}{suffix}", ""]
    if not teacher:
        lines.append("[试卷抬头]")
    lines.append(f"> {subtitle}" + (f" ｜ {notice}" if notice else ""))
    lines.append("")

    q_global = 0
    for s_idx, sec in enumerate(data.get("sections", []), 1):
        sec_title = sec.get("title", f"第{s_idx}部分")
        items = sec.get("items", [])
        sec_pts = round(sum(float(it.get("points", 0)) for it in items), 2)
        pts_str = int(sec_pts) if float(sec_pts).is_integer() else sec_pts
        lines.append(f"## {sec_title}（共 {len(items)} 题，计 {pts_str} 分）")
        if sec.get("instruction"):
            lines.append(f"> {sec['instruction']}")
        lines.append("")

        for item in items:
            q_global += 1
            num_label = item.get("id") or f"{q_global}."
            pts = float(item.get("points", 0))
            p_str = int(pts) if pts.is_integer() else pts
            stem = str(item.get("stem", "")).strip()
            lines.append(f"**{num_label} （{p_str} 分）** {stem}")

            opts = item.get("options") or []
            if opts:
                if all(len(str(o)) <= 16 for o in opts) and len(opts) <= 4:
                    lines.append("    ".join(str(o) for o in opts))
                else:
                    for o in opts:
                        lines.append(f"- {o}")

            if teacher:
                lines.append(f"【答案】{item.get('answer', '')}")
                if item.get("analysis"):
                    lines.append(f"【解析】{item['analysis']}")
                if item.get("rubric"):
                    lines.append(f"【评分标准】{item['rubric']}")
                if item.get("pitfall"):
                    lines.append(f"【易错警示】{item['pitfall']}")
            else:
                ans_lines = int(item.get("answer_lines", 0))
                if ans_lines > 0:
                    lines.append(f"[答题线:{ans_lines}]")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def verify_grading(records_path: pathlib.Path) -> tuple[dict, dict]:
    data = json.loads(records_path.read_text(encoding="utf-8-sig"))
    students = data.get("students", [])
    max_scores = data.get("item_max_scores", {})
    errors = []
    totals = []
    all_tags: list[str] = []
    item_buckets: dict[str, list[float]] = {}

    if not students:
        errors.append("students 列表为空")

    for stu in students:
        name = stu.get("name", "<未命名>")
        item_scores = stu.get("item_scores", {})
        calc_total = round(sum(float(v) for v in item_scores.values()), 2)
        declared_total = round(float(stu.get("total", calc_total)), 2)
        if abs(calc_total - declared_total) > 1e-6:
            errors.append(f"{name}: 小题得分之和 {calc_total} != 声明总分 {declared_total}")
        totals.append(calc_total)

        for k, v in item_scores.items():
            fv = float(v)
            if fv < 0:
                errors.append(f"{name}: 题号 {k} 出现负分 ({fv})")
            if k in max_scores and fv > float(max_scores[k]) + 1e-6:
                errors.append(f"{name}: 题号 {k} 得分 {fv} 超过满分 {max_scores[k]}")
            item_buckets.setdefault(k, []).append(fv)

        error_tags = stu.get("error_tags", {})
        for tag, lost_items in error_tags.items():
            if not lost_items:
                errors.append(f"{name}: 错因标签 '{tag}' 关联题号为空")
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
    sorted_tags = sorted(
        all_tags,
        key=lambda t: (-sum(1 for s in students if t in s.get("error_tags", {})), all_tags.index(t)),
    )
    for tag in sorted_tags:
        affected = [s.get("name", "") for s in students if tag in s.get("error_tags", {})]
        error_summary[tag] = {
            "count": len(affected),
            "ratio": f"{len(affected)}/{n}",
            "percent": f"{round(len(affected) * 100.0 / n, 1)}%" if n else "0%",
            "students": affected,
        }

    item_summary = {}
    for k, vals in item_buckets.items():
        avg_v = round(sum(vals) / len(vals), 2) if vals else 0.0
        entry = {"mean_score": avg_v}
        if k in max_scores and float(max_scores[k]) > 0:
            entry["max_score"] = float(max_scores[k])
            entry["score_rate"] = f"{round(avg_v * 100.0 / float(max_scores[k]), 1)}%"
        item_summary[k] = entry

    report = {
        "passed": len(errors) == 0,
        "mode": "grading",
        "student_count": n,
        "mean": mean_score,
        "median": median_score,
        "max": max(totals) if totals else 0.0,
        "min": min(totals) if totals else 0.0,
        "item_summary": item_summary,
        "error_summary": error_summary,
        "errors": errors,
    }
    return report, data


def render_grading_summary_markdown(report: dict, data: dict) -> str:
    title = data.get("title", "班级批量阅卷与学情诊断报告")
    sample_note = data.get("sample_note", "")
    lines = [f"# {title}", ""]
    if sample_note:
        lines.append(f"> {sample_note}")
        lines.append("")

    lines.extend([
        "## 一、全班整体成绩单源统计",
        "",
        "| 统计维度 | 数值 |",
        "| --- | --- |",
        f"| 参测人数 | {report['student_count']} 人 |",
        f"| 平均分 | {report['mean']} 分 |",
        f"| 中位数 | {report['median']} 分 |",
        f"| 最高分 / 最低分 | {report['max']} 分 / {report['min']} 分 |",
        "",
        "## 二、学生个体得分与核心失分标签台账",
        "",
        "| 姓名 | 总分 | 主要错因标签 |",
        "| --- | --- | --- |",
    ])
    for stu in data.get("students", []):
        tags = "；".join(f"{t}（{','.join(map(str, qs))}）" for t, qs in stu.get("error_tags", {}).items()) or "满分无失误"
        lines.append(f"| {stu.get('name', '')} | **{stu.get('total', '')}** | {tags} |")

    lines.extend([
        "",
        "## 三、高频共性错因单源归因表（按影响人数降序）",
        "",
        "| 排名 | 错因标签 | 涉及人数（占比） | 涉及学生名单 |",
        "| --- | --- | --- | --- |",
    ])
    for idx, (tag, info) in enumerate(report["error_summary"].items(), 1):
        lines.append(f"| TOP {idx} | **{tag}** | {info['ratio']}（{info['percent']}） | {'、'.join(info['students'])} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)

    p_exam = sub.add_parser("exam", help="Validate exam JSON points sum and optionally export student/teacher Markdown")
    p_exam.add_argument("json_path", type=pathlib.Path)
    p_exam.add_argument("--target-total", type=float, default=100.0)
    p_exam.add_argument("--export-student-md", type=pathlib.Path, default=None)
    p_exam.add_argument("--export-teacher-md", type=pathlib.Path, default=None)

    p_grad = sub.add_parser("grading", help="Validate student grading records and compute single-source error counts")
    p_grad.add_argument("json_path", type=pathlib.Path)
    p_grad.add_argument("--export-summary-md", type=pathlib.Path, default=None)

    args = ap.parse_args()

    if args.mode == "exam":
        res, raw_data = verify_exam(args.json_path, args.target_total)
        if res["passed"]:
            if args.export_student_md:
                args.export_student_md.parent.mkdir(parents=True, exist_ok=True)
                args.export_student_md.write_text(render_exam_markdown(raw_data, teacher=False), encoding="utf-8")
                res["student_md"] = str(args.export_student_md)
            if args.export_teacher_md:
                args.export_teacher_md.parent.mkdir(parents=True, exist_ok=True)
                args.export_teacher_md.write_text(render_exam_markdown(raw_data, teacher=True), encoding="utf-8")
                res["teacher_md"] = str(args.export_teacher_md)
    else:
        res, raw_data = verify_grading(args.json_path)
        if res["passed"] and args.export_summary_md:
            args.export_summary_md.parent.mkdir(parents=True, exist_ok=True)
            args.export_summary_md.write_text(render_grading_summary_markdown(res, raw_data), encoding="utf-8")
            res["summary_md"] = str(args.export_summary_md)

    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
