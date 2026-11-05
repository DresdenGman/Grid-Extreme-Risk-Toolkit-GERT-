#!/usr/bin/env python3
"""Aggregate GERT Historical Lab pilot feedback into summary.json.

Input: a Google Forms API export pair (form.json + responses.json) for the
"GERT Historical Lab - Participant Feedback" form. The raw export is NOT
shipped in this repository: the form's optional name/contact question can
contain identifying details. Only the aggregates written here are published.

Usage:
    python3 analyze_feedback.py FORM_JSON RESPONSES_JSON [OUTPUT_JSON]

Stdlib only. Percentages are shares of the respondents who answered the
question; scale questions report the mean and the full 1-5 distribution.
"""
import collections
import json
import statistics
import sys


def main() -> None:
    form = json.load(open(sys.argv[1]))
    responses = json.load(open(sys.argv[2]))["responses"]
    out_path = sys.argv[3] if len(sys.argv) > 3 else "summary.json"

    questions = {}
    for item in form.get("items", []):
        q = item.get("questionItem", {}).get("question", {})
        if q:
            questions[q["questionId"]] = item["title"]

    per_question = collections.defaultdict(list)
    for resp in responses:
        for qid, ans in (resp.get("answers") or {}).items():
            for v in ans.get("textAnswers", {}).get("answers", []):
                per_question[qid].append(v["value"])

    summary = {"responses": len(responses), "questions": {}}
    for qid, title in questions.items():
        vals = per_question.get(qid, [])
        entry = {"title": title, "answers": len(vals)}
        if vals and all(v.isdigit() and 1 <= int(v) <= 5 for v in vals):
            nums = [int(v) for v in vals]
            entry["mean"] = round(statistics.mean(nums), 2)
            entry["median"] = statistics.median(nums)
            entry["distribution"] = dict(sorted(collections.Counter(vals).items()))
        elif vals and len(set(vals)) <= 10:
            entry["counts"] = dict(collections.Counter(vals).most_common())
            entry["percent"] = {
                k: round(100.0 * c / len(vals), 1)
                for k, c in collections.Counter(vals).most_common()
            }
        else:
            entry["type"] = "free_text"
        summary["questions"][title] = entry

    with open(out_path, "w") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    print(f"wrote {out_path}: {summary['responses']} responses, "
          f"{len(summary['questions'])} questions")


if __name__ == "__main__":
    main()
