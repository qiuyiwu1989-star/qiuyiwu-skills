#!/usr/bin/env python3
"""KANO questionnaire scorer.

Input CSV (long format) columns: respondent, segment(optional), feature, functional, dysfunctional
Answers: 1-5 (1 like, 2 must-be/expect, 3 neutral, 4 live-with, 5 dislike) or Chinese text.
Output: markdown report with category distribution, main category, Better/Worse, quadrant, priority.

Usage: python3 kano_score.py responses.csv [-o result.md] [--threshold mean|0.5]
"""
import argparse
import csv
import sys
from collections import Counter, defaultdict

TEXT_MAP = {
    "喜欢": 1, "我很喜欢": 1, "like": 1,
    "理所当然": 2, "应该的": 2, "must-be": 2, "expect": 2,
    "无所谓": 3, "neutral": 3,
    "勉强接受": 4, "能忍受": 4, "live-with": 4,
    "不喜欢": 5, "我很不喜欢": 5, "dislike": 5,
}

# rows: functional answer 1..5 ; cols: dysfunctional answer 1..5
TABLE = [
    ["Q", "A", "A", "A", "O"],
    ["R", "I", "I", "I", "M"],
    ["R", "I", "I", "I", "M"],
    ["R", "I", "I", "I", "M"],
    ["R", "R", "R", "R", "Q"],
]
NAMES = {"M": "必备型", "O": "期望型", "A": "兴奋型", "I": "无差异", "R": "反向", "Q": "可疑"}
TIE_ORDER = ["M", "O", "A", "I", "R", "Q"]  # tie-break: M > O > A > I


def parse(v):
    v = str(v).strip()
    if v.isdigit() and 1 <= int(v) <= 5:
        return int(v)
    if v in TEXT_MAP:
        return TEXT_MAP[v]
    raise ValueError(f"无法识别的答案: {v!r}")


def analyze(rows):
    counts = defaultdict(Counter)
    for r in rows:
        cat = TABLE[parse(r["functional"]) - 1][parse(r["dysfunctional"]) - 1]
        counts[r["feature"].strip()][cat] += 1
    results = []
    for feat, c in counts.items():
        valid = c["A"] + c["O"] + c["M"] + c["I"]
        better = (c["A"] + c["O"]) / valid if valid else 0.0
        worse = -(c["O"] + c["M"]) / valid if valid else 0.0
        main = max(TIE_ORDER, key=lambda k: (c[k] if k != "Q" else -1, -TIE_ORDER.index(k)))
        results.append({"feature": feat, "c": c, "n": sum(c.values()), "better": better,
                        "worse": worse, "main": main})
    return results


def classify(results, mode):
    if mode == "mean" and results:
        bt = sum(r["better"] for r in results) / len(results)
        wt = sum(abs(r["worse"]) for r in results) / len(results)
    else:
        bt = wt = 0.5
    for r in results:
        hb, hw = r["better"] >= bt, abs(r["worse"]) >= wt
        if hb and hw:
            r["quad"], r["prio"], r["rank"] = "期望型区", "P1 优先做", 0
        elif hw:
            r["quad"], r["prio"], r["rank"] = "必备型区", "P1 必须做（门槛）", 1
        elif hb:
            r["quad"], r["prio"], r["rank"] = "兴奋型区", "P2 选做惊喜", 2
        else:
            r["quad"], r["prio"], r["rank"] = "无差异区", "P3 不做", 3
        if r["main"] == "R":
            r["prio"], r["rank"] = "风险：反向需求，勿做或可关闭", 4
    results.sort(key=lambda r: (r["rank"], -(r["better"] + abs(r["worse"]))))
    return bt, wt


def render(title, results, bt, wt):
    out = [f"### {title}", "", f"象限分界：Better={bt:.2f}，|Worse|={wt:.2f}", "",
           "| 需求 | 样本 | A | O | M | I | R | Q | 主类别 | Better | Worse | 象限 | 建议 |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        c = r["c"]
        warn = "（样本<15，仅供参考）" if r["n"] < 15 else ""
        out.append(f"| {r['feature']} | {r['n']}{warn} | {c['A']} | {c['O']} | {c['M']} | {c['I']} | "
                   f"{c['R']} | {c['Q']} | {NAMES[r['main']]} | {r['better']:.2f} | {r['worse']:.2f} | "
                   f"{r['quad']} | {r['prio']} |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="KANO 问卷统计")
    ap.add_argument("csv")
    ap.add_argument("-o", "--output")
    ap.add_argument("--threshold", choices=["mean", "0.5"], default="mean")
    a = ap.parse_args()
    with open(a.csv, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("CSV 为空")
    groups = defaultdict(list)
    for r in rows:
        groups[(r.get("segment") or "全部").strip() or "全部"].append(r)
    parts = ["# KANO 分析结果", ""]
    if len(groups) > 1:
        groups = {"全部人群": rows, **groups}
    for seg, rs in groups.items():
        res = analyze(rs)
        bt, wt = classify(res, a.threshold)
        parts.append(render(seg, res, bt, wt))
    report = "\n".join(parts)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"已写入 {a.output}")
    print(report)


if __name__ == "__main__":
    main()
