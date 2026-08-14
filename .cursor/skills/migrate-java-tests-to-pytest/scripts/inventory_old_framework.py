"""Scan the legacy Java/TestNG framework and write migration/inventory.json.

The inventory is the denominator of every migration percentage: one row per Java
@Test method, plus per-layer counts so the size of the remaining work is visible.

Usage:
    python .cursor/skills/migrate-java-tests-to-pytest/scripts/inventory_old_framework.py
    python ... /inventory_old_framework.py --old-root ../legacy --out migration/inventory.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

DEFAULT_OLD_ROOT = "c1-playwright-automation-old-framework"

# BaseTest exposes one accessor per steps class; a call to any of them means the
# test drives a browser. Same idea for the API side.
UI_ACCESSORS = (
    "getPage", "getPageFactory", "stepFactory", "uiCommonSteps", "hybridSteps",
    "createBRSteps", "businessRequestActionMenuSteps", "workspaceEntitySteps",
    "searchCatalogSteps", "approvalFlowSteps", "businessRequestSteps",
    "genericEntitySteps", "genericEntitySourceTableLightBoxSteps",
    "businessValidationSteps", "toolBoxSideMenuSteps", "priceSteps",
    "promotionSteps", "billDiscountSteps", "dataStreamsSteps", "priceGroupSteps",
    "termSteps", "offerGroupSteps", "charSteps", "conflictResolutionSteps",
    "commercialRelationSteps", "searchSteps", "ruleSteps",
    "publishToTestEnvironmentSteps", "abacSteps", "auditSteps",
    "categoriesSteps", "importExportSteps", "dashUISteps", "loginIntoDashBoard",
)
API_ACCESSORS = (
    "apiStepFactory", "genericAPI", "entitySearch", "genericApiSteps",
    "entitySearchApiSteps", "brSteps", "importApiSteps", "couchbaseSteps",
    "categoryApiSteps", "offerGroupApiSteps", "rulesPromotionApiSteps",
)

# layer name -> (path under src/main/java/com, description)
LAYERS = {
    "test_classes": "testFlows",
    "elements": "ui/base/baseElements",
    "pages": "ui/pages",
    "steps": "ui/steps",
    "api_steps": "api/steps",
    "api_entities": "api/entities",
    "data_classes": "data",
    "infrastructure": "infrastructure",
}

PUBLIC_METHOD = re.compile(r"^\s*public\s+(?!class|enum|interface|record)[\w<>\[\],.\s]+\s+\w+\s*\(", re.MULTILINE)
METHOD_SIGNATURE = re.compile(
    r"(?:public|protected|private)\s+(?:static\s+|final\s+|synchronized\s+)*"
    r"[\w<>\[\],.\s]+?\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w.,\s]+)?\s*\{"
)
CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\.\s*([A-Za-z_]\w*)\s*\(")
NO_ARG_ACCESSOR = re.compile(r"\b([A-Za-z_]\w*)\s*\(\s*\)")


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments without touching string literals."""
    out = []
    i, n = 0, len(text)
    while i < n:
        char = text[i]
        if char == '"' or char == "'":
            quote = char
            out.append(char)
            i += 1
            while i < n:
                out.append(text[i])
                if text[i] == "\\":
                    i += 1
                    if i < n:
                        out.append(text[i])
                        i += 1
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if char == "/" and i + 1 < n:
            if text[i + 1] == "/":
                while i < n and text[i] != "\n":
                    i += 1
                continue
            if text[i + 1] == "*":
                end = text.find("*/", i + 2)
                i = n if end == -1 else end + 2
                # keep newlines so line numbers stay usable
                out.append("\n")
                continue
        out.append(char)
        i += 1
    return "".join(out)


def match_balanced(text: str, start: int, opening: str, closing: str) -> int:
    """Return the index just past the balanced pair that starts at `start`."""
    depth = 0
    i = start
    n = len(text)
    while i < n:
        char = text[i]
        if char in ('"', "'"):
            quote = char
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    break
                i += 1
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def parse_annotation_args(text: str, at_index: int) -> tuple[str, int]:
    """Return (args_text, index_after_annotation) for an annotation at `at_index`."""
    i = at_index
    while i < len(text) and text[i] not in "(\n":
        i += 1
    if i < len(text) and text[i] == "(":
        end = match_balanced(text, i, "(", ")")
        if end != -1:
            return text[i + 1:end - 1], end
    return "", at_index


def extract_groups(args: str) -> list[str]:
    braced = re.search(r"groups\s*=\s*\{(.*?)\}", args, re.DOTALL)
    raw = braced.group(1) if braced else ""
    if not braced:
        single = re.search(r'groups\s*=\s*"([^"]*)"', args)
        raw = f'"{single.group(1)}"' if single else ""
    return [value.strip().strip('"') for value in raw.split(",") if value.strip().strip('"')]


def collect_calls(body: str, limit: int = 60) -> list[str]:
    """Best-effort list of `receiver.method` calls plus the factory accessors used."""
    seen: dict[str, None] = {}
    for receiver, method in CALL.findall(body):
        if receiver in ("System", "Assert", "assertThat", "String", "Math", "Arrays", "List"):
            continue
        seen.setdefault(f"{receiver}.{method}", None)
    for accessor in NO_ARG_ACCESSOR.findall(body):
        if accessor in UI_ACCESSORS or accessor in API_ACCESSORS:
            seen.setdefault(f"{accessor}()", None)
    return list(seen)[:limit]


def classify(body: str, class_name: str) -> str:
    has_ui = any(re.search(rf"\b{name}\s*\(", body) for name in UI_ACCESSORS)
    has_api = any(re.search(rf"\b{name}\s*\(", body) for name in API_ACCESSORS)
    if has_ui and has_api:
        return "e2e"
    if has_ui:
        return "ui"
    if has_api:
        return "api"
    lowered = class_name.lower()
    if "api" in lowered:
        return "api"
    if "ui" in lowered or "dashboard" in lowered:
        return "ui"
    return "unknown"


def scan_test_file(path: Path, java_root: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = strip_comments(raw)
    package = re.search(r"package\s+([\w.]+)\s*;", text)
    package_name = package.group(1) if package else "unknown"
    class_name = path.stem

    tests = []
    for match in re.finditer(r"@Test\b", text):
        args, after = parse_annotation_args(text, match.end())
        signature = METHOD_SIGNATURE.search(text, after)
        if not signature:
            continue
        method = signature.group(1)
        body_end = match_balanced(text, signature.end() - 1, "{", "}")
        body = text[signature.end():body_end - 1] if body_end != -1 else ""

        description = re.search(r'description\s*=\s*"((?:[^"\\]|\\.)*)"', args)
        provider = re.search(r'dataProvider\s*=\s*"(\w+)"', args)
        priority = re.search(r"priority\s*=\s*(-?\d+)", args)

        tests.append({
            "old": f"{package_name}.{class_name}#{method}",
            "class": class_name,
            "method": method,
            "file": str(path.relative_to(java_root.parents[3])).replace("\\", "/"),
            "line": text.count("\n", 0, match.start()) + 1,
            "kind": classify(body, class_name),
            "groups": extract_groups(args),
            "description": description.group(1) if description else "",
            "data_provider": provider.group(1) if provider else None,
            "priority": int(priority.group(1)) if priority else None,
            "retry_analyzer": "retryAnalyzer" in args,
            "body_lines": body.count("\n") + 1 if body else 0,
            "calls": collect_calls(body),
        })
    return tests


def count_layer(java_root: Path, relative: str) -> dict:
    directory = java_root / relative
    if not directory.exists():
        return {"files": 0, "public_methods": 0}
    files = [p for p in directory.rglob("*.java")]
    methods = 0
    for path in files:
        text = strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
        methods += len(PUBLIC_METHOD.findall(text))
    return {"files": len(files), "public_methods": methods}


def read_tag_aliases(resources: Path) -> dict[str, list[str]]:
    tag_file = resources / "testTag" / "testsTag.yaml"
    if not tag_file.exists():
        return {}
    aliases: dict[str, list[str]] = {}
    current = None
    for line in tag_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        header = re.match(r"^([\w.-]+)\s*:\s*$", line)
        if header:
            current = header.group(1)
            aliases[current] = []
            continue
        item = re.match(r"^\s*-\s*(.+?)\s*$", line)
        if item and current:
            aliases[current].append(item.group(1).strip().strip('"'))
    return aliases


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory the legacy Java test suite.")
    parser.add_argument("--old-root", default=DEFAULT_OLD_ROOT, help="legacy framework root")
    parser.add_argument("--repo-root", default=".", help="this repository's root")
    parser.add_argument("--out", default="migration/inventory.json", help="output JSON path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    old_root = Path(args.old_root)
    if not old_root.is_absolute():
        old_root = (repo_root / old_root).resolve()
    java_root = old_root / "src" / "main" / "java" / "com"
    if not java_root.exists():
        print(f"ERROR: no Java sources at {java_root}")
        return 1

    test_dir = java_root / "testFlows"
    test_files = sorted(
        path for path in test_dir.rglob("*.java")
        if path.stem not in ("BaseTest", "BaseApiTest")
    )

    tests: list[dict] = []
    for path in test_files:
        tests.extend(scan_test_file(path, java_root))

    groups: dict[str, int] = {}
    kinds: dict[str, int] = {}
    for test in tests:
        kinds[test["kind"]] = kinds.get(test["kind"], 0) + 1
        for group in test["groups"] or ["(no group)"]:
            groups[group] = groups.get(group, 0) + 1

    resources = old_root / "src" / "main" / "resources"
    payloads = list((resources / "payloads").rglob("*.json")) if (resources / "payloads").exists() else []

    inventory = {
        "schema": 1,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "old_root": str(old_root).replace("\\", "/"),
        "totals": {
            "test_files": len(test_files),
            "tests": len(tests),
            "payload_files": len(payloads),
        },
        "kinds": dict(sorted(kinds.items())),
        "layers": {name: count_layer(java_root, relative) for name, relative in LAYERS.items()},
        "groups": dict(sorted(groups.items(), key=lambda item: (-item[1], item[0]))),
        "tag_aliases": read_tag_aliases(resources),
        "tests": tests,
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = repo_root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"inventory written: {out_path}")
    print(f"  test files      : {len(test_files)}")
    print(f"  @Test methods   : {len(tests)}")
    print(f"  kinds           : " + ", ".join(f"{k}={v}" for k, v in inventory["kinds"].items()))
    print(f"  payload files   : {len(payloads)}")
    for name, counts in inventory["layers"].items():
        print(f"  {name:<16}: {counts['files']} files, {counts['public_methods']} public methods")
    top_groups = list(inventory["groups"].items())[:8]
    print("  largest groups  : " + ", ".join(f"{name} ({count})" for name, count in top_groups))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
