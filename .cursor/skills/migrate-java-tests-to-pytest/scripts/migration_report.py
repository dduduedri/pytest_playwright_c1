"""Score the Java -> pytest migration and write migration/MIGRATION_REPORT.md.

    python .cursor/skills/migrate-java-tests-to-pytest/scripts/migration_report.py --init
    python ... /migration_report.py
    python ... /migration_report.py --junit reports-results/junit.xml

--init creates migration/ledger.json from the inventory (existing rows are kept).
--junit promotes ledger rows from an actual pytest run, so the headline number is
evidence-based rather than self-reported.
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ElementTree
from datetime import datetime
from pathlib import Path

MIGRATED_STATUSES = ("code_complete", "verified", "failing")
ALL_STATUSES = ("not_started", "in_progress", "code_complete", "verified", "failing", "blocked")

# gate id -> (description, globs, forbidden pattern)
GATES = (
    ("G1", "no time.sleep",
     ("tests/**/*.py", "ui/**/*.py", "api/**/*.py", "utils/**/*.py", "fixtures/**/*.py"),
     r"\btime\.sleep\s*\("),
    ("G2", "no raw selectors in tests",
     ("tests/**/*.py",),
     r"\bpage\.(?:locator|get_by_\w+)\s*\(|context_setup\.(?:locator|get_by_\w+)\s*\("),
    ("G3", "no stubs left behind",
     ("tests/**/*.py", "ui/**/*.py", "api/**/*.py", "utils/**/*.py", "fixtures/**/*.py"),
     r"\bTODO\b|\bFIXME\b|NotImplementedError"),
    ("G6", "no {{...}} placeholders in payloads",
     ("data/api_payloads/**/*.json",),
     r"\{\{[^}]+\}\}"),
    ("G7", "no password in parametrize",
     ("tests/**/*.py",),
     r"parametrize\s*\(\s*[\"'][^\"']*password"),
    ("G8", "no ported factory classes",
     ("ui/**/*.py", "api/**/*.py"),
     r"^\s*class\s+\w*Factory\b"),
)

KIND_MARKER = re.compile(r"@pytest\.mark\.(ui|api|e2e)\b")
ALLURE_TITLE = re.compile(r"@allure\.title\s*\(")
SKIP_MARKER = re.compile(r"@pytest\.mark\.skip\b")


def read_json(path: Path):
    if not path.exists():
        raise SystemExit(f"ERROR: {path} not found. Run inventory_old_framework.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- ledger


def init_ledger(inventory: dict, ledger_path: Path) -> dict:
    existing = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
    by_old = {row["old"]: row for row in existing.get("tests", [])}

    rows = []
    for test in inventory["tests"]:
        row = by_old.get(test["old"])
        if row is None:
            row = {
                "old": test["old"],
                "status": "not_started",
                "new": "",
                "markers": [],
                "symbols": [],
                "notes": "",
                "blocked_reason": None,
            }
        rows.append(row)

    ledger = {
        "schema": 1,
        "updated": datetime.now().isoformat(timespec="seconds"),
        "tests": rows,
        "out_of_scope": existing.get("out_of_scope", []),
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")
    added = len(rows) - len(by_old)
    print(f"ledger written: {ledger_path} ({len(rows)} rows, {max(added, 0)} new)")
    return ledger


# ---------------------------------------------------------------- junit


def junit_node_id(repo_root: Path, classname: str, name: str) -> str:
    parts = [part for part in classname.split(".") if part]
    for cut in range(len(parts), 0, -1):
        candidate = Path(*parts[:cut]).with_suffix(".py")
        if (repo_root / candidate).exists():
            tail = parts[cut:] + [name]
            return "::".join([str(candidate).replace("\\", "/")] + tail)
    return f"{classname}::{name}"


def read_junit(repo_root: Path, junit_path: Path) -> dict[str, str]:
    """Return {node_id: passed|failed|skipped}."""
    root = ElementTree.parse(junit_path).getroot()
    outcomes: dict[str, str] = {}
    for case in root.iter("testcase"):
        node = junit_node_id(repo_root, case.get("classname", ""), case.get("name", ""))
        if case.find("failure") is not None or case.find("error") is not None:
            outcomes[node] = "failed"
        elif case.find("skipped") is not None:
            outcomes[node] = "skipped"
        else:
            outcomes[node] = "passed"
    return outcomes


def apply_junit(ledger: dict, outcomes: dict[str, str]) -> int:
    updated = 0
    for row in ledger["tests"]:
        target = row.get("new") or ""
        if not target:
            continue
        matched = [
            result for node, result in outcomes.items()
            if node == target or node.startswith(f"{target}[")
        ]
        if not matched:
            continue
        if "failed" in matched:
            status, reason = "failing", row.get("blocked_reason")
        elif all(result == "skipped" for result in matched):
            status, reason = "blocked", "skipped in run"
        else:
            status, reason = "verified", None
        if row["status"] != status:
            row["status"], row["blocked_reason"] = status, reason
            updated += 1
    return updated


# ---------------------------------------------------------------- symbols


def resolve_symbol(repo_root: Path, target: str) -> tuple[bool, str]:
    if "::" not in target:
        return False, "expected '<path>::<Class>.<method>' or '<path>::<function>'"
    path_part, symbol = target.split("::", 1)
    path = repo_root / path_part
    if not path.exists():
        return False, f"missing file {path_part}"
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "." in symbol:
        class_name, method = symbol.split(".", 1)
        if not re.search(rf"^\s*class\s+{re.escape(class_name)}\b", text, re.MULTILINE):
            return False, f"class {class_name} not found in {path_part}"
        if not re.search(rf"^\s*def\s+{re.escape(method)}\s*\(", text, re.MULTILINE):
            return False, f"method {method} not found in {path_part}"
        return True, ""
    if not re.search(rf"^\s*def\s+{re.escape(symbol)}\s*\(", text, re.MULTILINE):
        return False, f"function {symbol} not found in {path_part}"
    return True, ""


# ---------------------------------------------------------------- gates


def iter_files(repo_root: Path, globs) -> list[Path]:
    files: list[Path] = []
    for pattern in globs:
        files.extend(
            path for path in repo_root.glob(pattern)
            if path.is_file() and ".venv" not in path.parts and "__pycache__" not in path.parts
        )
    return sorted(set(files))


def run_pattern_gates(repo_root: Path) -> list[dict]:
    results = []
    for gate_id, description, globs, pattern in GATES:
        regex = re.compile(pattern, re.MULTILINE)
        hits = []
        for path in iter_files(repo_root, globs):
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if regex.search(line):
                    hits.append(f"{path.relative_to(repo_root).as_posix()}:{number}: {line.strip()[:100]}")
        results.append({
            "id": gate_id, "description": description,
            "passed": not hits, "hits": hits[:5], "hit_count": len(hits),
        })
    return results


def run_ledger_gates(repo_root: Path, ledger: dict) -> list[dict]:
    files = []
    for row in ledger["tests"]:
        if row["status"] in MIGRATED_STATUSES and row.get("new"):
            candidate = row["new"].split("::")[0]
            if (repo_root / candidate).exists():
                files.append(repo_root / candidate)
    files = sorted(set(files))

    missing_meta, still_skipped = [], []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(repo_root).as_posix()
        if not KIND_MARKER.search(text):
            missing_meta.append(f"{relative}: no @pytest.mark.ui/api/e2e")
        if not ALLURE_TITLE.search(text):
            missing_meta.append(f"{relative}: no @allure.title")
        if SKIP_MARKER.search(text):
            still_skipped.append(f"{relative}: @pytest.mark.skip in a migrated test")
    return [
        {"id": "G4", "description": "migrated tests carry a kind marker and @allure.title",
         "passed": not missing_meta, "hits": missing_meta[:5], "hit_count": len(missing_meta)},
        {"id": "G5", "description": "migrated tests are not skipped",
         "passed": not still_skipped, "hits": still_skipped[:5], "hit_count": len(still_skipped)},
    ]


# ---------------------------------------------------------------- scoring


def percent(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def build_stats(repo_root: Path, inventory: dict, ledger: dict) -> dict:
    by_old = {row["old"]: row for row in ledger["tests"]}
    out_of_scope = {entry["old"] for entry in ledger.get("out_of_scope", [])}

    counts = {status: 0 for status in ALL_STATUSES}
    per_group: dict[str, dict] = {}
    per_kind: dict[str, dict] = {}
    blocked, unresolved, declared, resolved = [], [], 0, 0

    for test in inventory["tests"]:
        row = by_old.get(test["old"])
        status = "out_of_scope" if test["old"] in out_of_scope else (row["status"] if row else "not_started")
        if status != "out_of_scope":
            counts[status] = counts.get(status, 0) + 1
            for group in test["groups"] or ["(no group)"]:
                bucket = per_group.setdefault(group, {"total": 0, "verified": 0})
                bucket["total"] += 1
                bucket["verified"] += status == "verified"
            bucket = per_kind.setdefault(test["kind"], {"total": 0, "verified": 0})
            bucket["total"] += 1
            bucket["verified"] += status == "verified"
        if status == "blocked" and row:
            blocked.append({"old": test["old"], "reason": row.get("blocked_reason") or "(no reason recorded)"})
        if row:
            for symbol in row.get("symbols", []):
                declared += 1
                ok, why = resolve_symbol(repo_root, symbol.get("new", ""))
                if ok:
                    resolved += 1
                else:
                    unresolved.append({"old": symbol.get("old", "?"), "new": symbol.get("new", ""), "reason": why})

    stale = [old for old in by_old if old not in {test["old"] for test in inventory["tests"]}]
    total = len(inventory["tests"])
    in_scope = total - len(out_of_scope)

    return {
        "total_java_tests": total,
        "out_of_scope": len(out_of_scope),
        "in_scope": in_scope,
        "counts": counts,
        "migration_score": percent(counts["verified"], in_scope),
        "code_coverage": percent(counts["verified"] + counts["code_complete"], in_scope),
        "symbols": {
            "declared": declared, "resolved": resolved,
            "resolution": percent(resolved, declared), "unresolved": unresolved[:20],
        },
        "per_group": dict(sorted(per_group.items(), key=lambda item: (-item[1]["total"], item[0]))),
        "per_kind": dict(sorted(per_kind.items())),
        "blocked": blocked,
        "stale_ledger_rows": stale,
    }


def suggest_next(stats: dict) -> str:
    started = [
        (name, data) for name, data in stats["per_group"].items()
        if data["verified"] and data["verified"] < data["total"]
    ]
    pool = started or [
        (name, data) for name, data in stats["per_group"].items() if data["verified"] < data["total"]
    ]
    if not pool:
        return "nothing left in scope"
    name, data = max(pool, key=lambda item: item[1]["total"] - item[1]["verified"])
    remaining = data["total"] - data["verified"]
    shared = " (shares pages already migrated)" if data["verified"] else ""
    return f"group `{name}` - {remaining} of {data['total']} tests remaining{shared}"


# ---------------------------------------------------------------- rendering


def render_report(inventory: dict, ledger: dict, stats: dict, gates: list[dict], junit: str | None) -> str:
    counts = stats["counts"]
    lines = [
        "# Migration report - Java/TestNG -> pytest",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}  ",
        f"Legacy inventory: {inventory['generated']} ({inventory['old_root']})  ",
        f"Run evidence: {junit or 'none (statuses are self-reported - pass --junit for evidence)'}",
        "",
        "## Headline",
        "",
        f"**Migration score: {stats['migration_score']}%** "
        f"({counts['verified']} of {stats['in_scope']} in-scope tests verified green)",
        "",
        f"- Out of scope: {stats['out_of_scope']} test(s) - excluded from the denominator",
        f"- Code complete but unproven: {counts['code_complete']} ({stats['code_coverage']}% incl. verified)",
        f"- Symbol resolution: {stats['symbols']['resolved']}/{stats['symbols']['declared']} "
        f"({stats['symbols']['resolution']}%)",
        f"- Gates: {sum(1 for gate in gates if gate['passed'])}/{len(gates)} passing",
        "",
        "## Status breakdown",
        "",
        "| Status | Tests | Share of in-scope |",
        "|---|---:|---:|",
    ]
    for status in ALL_STATUSES:
        lines.append(f"| {status} | {counts.get(status, 0)} | {percent(counts.get(status, 0), stats['in_scope'])}% |")
    lines += [
        f"| out_of_scope | {stats['out_of_scope']} | - |",
        f"| **total Java @Test** | **{stats['total_java_tests']}** | |",
        "",
        "## By kind",
        "",
        "| Kind | Verified | Total | % |",
        "|---|---:|---:|---:|",
    ]
    for kind, data in stats["per_kind"].items():
        lines.append(f"| {kind} | {data['verified']} | {data['total']} | {percent(data['verified'], data['total'])}% |")

    lines += ["", "## By legacy TestNG group", "", "| Group | Verified | Total | % |", "|---|---:|---:|---:|"]
    for name, data in stats["per_group"].items():
        lines.append(f"| {name} | {data['verified']} | {data['total']} | {percent(data['verified'], data['total'])}% |")

    lines += ["", "## Convention gates", "", "| Gate | Check | Result | Hits |", "|---|---|---|---:|"]
    for gate in gates:
        lines.append(
            f"| {gate['id']} | {gate['description']} | "
            f"{'pass' if gate['passed'] else 'FAIL'} | {gate['hit_count']} |"
        )
    failing_gates = [gate for gate in gates if not gate["passed"]]
    if failing_gates:
        lines += ["", "### Gate findings", ""]
        for gate in failing_gates:
            lines.append(f"**{gate['id']} - {gate['description']}** ({gate['hit_count']} hit(s))")
            lines += [f"- `{hit}`" for hit in gate["hits"]]
            if gate["hit_count"] > len(gate["hits"]):
                lines.append(f"- ... {gate['hit_count'] - len(gate['hits'])} more")
            lines.append("")

    if stats["symbols"]["unresolved"]:
        lines += ["", "## Unresolved symbols", "",
                  "Ledger entries whose Python target does not exist - the test is not migrated in depth.", ""]
        for symbol in stats["symbols"]["unresolved"]:
            lines.append(f"- `{symbol['old']}` -> `{symbol['new']}`: {symbol['reason']}")

    if stats["blocked"]:
        lines += ["", "## Blocked", "", "| Java test | Reason |", "|---|---|"]
        for entry in stats["blocked"]:
            lines.append(f"| `{entry['old']}` | {entry['reason']} |")

    out_of_scope = ledger.get("out_of_scope", [])
    lines += ["", "## Out of scope", ""]
    if out_of_scope:
        lines += ["| Java test | Reason | Approved by |", "|---|---|---|"]
        for entry in out_of_scope:
            lines.append(
                f"| `{entry.get('old', '?')}` | {entry.get('reason', '(none)')} | "
                f"{entry.get('approved_by', 'NOT APPROVED')} |"
            )
    else:
        lines.append("None - every Java test is in scope.")

    if stats["stale_ledger_rows"]:
        lines += ["", "## Stale ledger rows", "",
                  "In the ledger but no longer in the legacy suite - re-run the inventory or remove them.", ""]
        lines += [f"- `{old}`" for old in stats["stale_ledger_rows"]]

    lines += ["", "## Next up", "", suggest_next(stats), ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description="Score the Java -> pytest migration.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--inventory", default="migration/inventory.json")
    parser.add_argument("--ledger", default="migration/ledger.json")
    parser.add_argument("--out", default="migration/MIGRATION_REPORT.md")
    parser.add_argument("--junit", default=None, help="pytest --junitxml file used as run evidence")
    parser.add_argument("--init", action="store_true", help="create/refresh the ledger from the inventory")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    inventory = read_json(repo_root / args.inventory)
    ledger_path = repo_root / args.ledger

    if args.init:
        init_ledger(inventory, ledger_path)
        return 0

    if not ledger_path.exists():
        raise SystemExit(f"ERROR: {ledger_path} not found. Run with --init first.")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    junit_label = None
    if args.junit:
        junit_path = repo_root / args.junit if not Path(args.junit).is_absolute() else Path(args.junit)
        if not junit_path.exists():
            raise SystemExit(f"ERROR: junit file not found: {junit_path}")
        outcomes = read_junit(repo_root, junit_path)
        changed = apply_junit(ledger, outcomes)
        ledger["updated"] = datetime.now().isoformat(timespec="seconds")
        ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")
        junit_label = f"{args.junit} ({len(outcomes)} test cases, {changed} ledger row(s) updated)"

    gates = run_pattern_gates(repo_root) + run_ledger_gates(repo_root, ledger)
    gates.sort(key=lambda gate: gate["id"])
    stats = build_stats(repo_root, inventory, ledger)

    out_path = repo_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_report(inventory, ledger, stats, gates, junit_label), encoding="utf-8")
    (out_path.parent / "report.json").write_text(
        json.dumps({"generated": datetime.now().isoformat(timespec="seconds"),
                    "stats": stats, "gates": gates}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    counts = stats["counts"]
    print(f"report written: {out_path}")
    print(f"MIGRATION SCORE: {stats['migration_score']}% "
          f"({counts['verified']}/{stats['in_scope']} in-scope tests verified)")
    print(f"  out of scope   : {stats['out_of_scope']}")
    print("  statuses       : " + ", ".join(f"{status}={counts.get(status, 0)}" for status in ALL_STATUSES))
    print(f"  symbols        : {stats['symbols']['resolved']}/{stats['symbols']['declared']} "
          f"({stats['symbols']['resolution']}%)")
    failed = [gate["id"] for gate in gates if not gate["passed"]]
    print(f"  gates          : {len(gates) - len(failed)}/{len(gates)} passing"
          + (f" (failing: {', '.join(failed)})" if failed else ""))
    print(f"  next up        : {suggest_next(stats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
