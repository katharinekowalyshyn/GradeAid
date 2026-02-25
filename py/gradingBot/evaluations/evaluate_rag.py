"""
Grade real homework submissions in courseMaterials and report pass/fail (binary).
Uploads materials, finds .txt submissions, grades each. Optional: --human-scores for comparison.

Run from the py/ directory:  python -m gradingBot.evaluations.evaluate_rag
Or:  cd py && python gradingBot/evaluations/evaluate_rag.py
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
_PKG_ROOT = _SCRIPT_DIR.parent
_PY_ROOT = _PKG_ROOT.parent  # py/ directory

# Ensure py/ is on path so "gradingBot" package is found
if str(_PY_ROOT) not in sys.path:
    sys.path.insert(0, str(_PY_ROOT))

# Load .env from py/ so LLMProxy finds credentials when run from project root
try:
    from dotenv import load_dotenv
    for _name in (".env", ".env."):
        _env_path = _PY_ROOT / _name
        if _env_path.exists():
            load_dotenv(dotenv_path=_env_path, override=True)
            break
except ImportError:
    pass

from gradingBot.gradingBot import GradingBot

def _find_submissions(materials_dir: Path) -> List[Path]:
    out = [p for p in materials_dir.rglob("*.txt") if not p.name.startswith("~$")]
    return sorted(out, key=lambda x: (x.parent.name, x.name))


def _upload_materials(bot: GradingBot, materials_dir: Path) -> None:
    if not materials_dir.exists():
        return
    for p in materials_dir.rglob("*.pdf"):
        if p.name.startswith("~$"):
            continue
        if "SOLUTIONS" in p.name or "solutions" in p.name.lower():
            bot.upload_homework_solution(p, assignment_name=p.stem[:30])
        else:
            bot.upload_homework_assignment(p, assignment_name=p.stem[:30])
    for p in materials_dir.rglob("*.txt"):
        if p.name.startswith("~$"):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace").strip()
            if t:
                bot.client.upload_text(text=t[:50000], session_id=bot.session_id, description=p.name, strategy="smart")
        except Exception:
            pass
    bot.wait_for_processing(seconds=30)


def _score_from_result(res: Dict[str, Any], max_pts: float) -> Optional[float]:
    if "error" in res:
        return None
    s = res.get("score")
    if s is not None:
        return s
    fb = res.get("feedback") or ""
    m = re.search(r"(\d+\.?\d*)\s*/\s*(\d+\.?\d*)", fb)
    if m:
        try:
            num, den = float(m.group(1)), float(m.group(2))
            return (num / den) * max_pts if den else None
        except ValueError:
            pass
    return None


def run(materials_dir: Path, upload: bool = True, human_scores: Optional[List[Dict]] = None) -> Dict[str, Any]:
    bot = GradingBot(session_id="evaluate_rag_session")
    if upload:
        _upload_materials(bot, materials_dir)
    human_by_id = {h["submission_id"]: h for h in (human_scores or []) if h.get("submission_id")}
    results = []
    for path in _find_submissions(materials_dir):
        sid = path.stem
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            results.append({"submission_id": sid, "grade": None, "total": None, "passed": False, "error": str(e), "feedback": None})
            continue
        if not content.strip():
            results.append({"submission_id": sid, "grade": None, "total": None, "passed": False, "error": "empty", "feedback": None})
            continue
        assignment = path.parent.name[:20] if path.parent != materials_dir else "HW"
        max_pts = human_by_id.get(sid, {}).get("max_points") or 100.0
        grading_instruction = (
            f"Grade this homework submission for {assignment}. Use the assignment and solutions in the course materials.\n\n"
            f"IMPORTANT: Assign points per problem or section by comparing to the solutions (e.g. 'Problem 1: 10/10, Problem 2: 7/15'). Sum them for the total. "
            f"Do NOT give the same score to every submission. Strong work = high score, partial/wrong = lower score. Maximum points = {max_pts:.0f}.\n\n"
            f"Provide your response in this exact format:\n"
            f"SCORE: [number] / {max_pts:.0f}\n\n"
            f"POINTS BY PART: [e.g. Problem 1: 10/10, Problem 2a: 5/5, Problem 2b: 0/5]\n\n"
            f"POINTS OFF: [Explain why points were deducted—what is missing, incorrect, or incomplete.]\n\n"
            f"QUESTIONS CORRECT: [List which questions or parts are correct.]\n\n"
            f"QUESTIONS INCORRECT: [List which questions or parts are wrong or incomplete.]\n\n"
            f"FEEDBACK: [Any additional brief feedback.]"
        )
        res = bot.grade_submission(
            question=grading_instruction,
            student_answer=content,
            max_points=max_pts,
            assignment_name=assignment,
        )
        score = _score_from_result(res, max_pts)
        feedback = (res.get("feedback") or "").strip()
        row = {
            "submission_id": sid,
            "grade": score,
            "total": max_pts,
            "passed": "error" not in res and score is not None,
            "feedback": feedback,
        }
        if res.get("error"):
            row["error"] = res["error"]
        if sid in human_by_id and (h := human_by_id[sid]).get("human_score") is not None and score is not None:
            row["human_score"] = h["human_score"]
            row["diff"] = round(score - h["human_score"], 2)
        results.append(row)
    n = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    return {"submissions_graded": n, "passed": passed, "results": results}


def main():
    import argparse
    p = argparse.ArgumentParser(description="Grade submissions in courseMaterials")
    p.add_argument("--no-upload", action="store_true", help="Skip uploading materials")
    p.add_argument("--human-scores", type=str, help="JSON file with submission_id, human_score, max_points")
    args = p.parse_args()
    materials_dir = _PKG_ROOT / "courseMaterials"
    if not materials_dir.exists():
        print("Not found:", materials_dir)
        return
    human = None
    if args.human_scores and Path(args.human_scores).exists():
        with open(args.human_scores) as f:
            human = json.load(f)
    report = run(materials_dir, upload=not args.no_upload, human_scores=human)
    out = _SCRIPT_DIR / "rag_evaluation_results.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print("Grades per submission (score / total):")
    for r in report["results"]:
        grade, total = r.get("grade"), r.get("total")
        if grade is not None and total is not None:
            g = f"{grade:.1f} / {total:.0f}"
        else:
            g = "—"
        print(f"\n  {r['submission_id']}: {g}")
        fb = r.get("feedback")
        if fb:
            print(f"  --- Feedback (points off, questions correct/incorrect) ---")
            print(f"  {fb[:1500]}" + ("..." if len(fb) > 1500 else ""))
    print(f"\nPassed: {report['passed']}/{report['submissions_graded']}. Wrote {out}")


if __name__ == "__main__":
    main()
