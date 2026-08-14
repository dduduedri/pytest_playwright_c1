# Ledger, gates and how the percentage is computed

Three files under `migration/` hold the state. Commit all three: they are the
migration's audit trail.

| File | Written by | Role |
|---|---|---|
| `inventory.json` | `inventory_old_framework.py` | the denominator: every Java `@Test` + layer counts. Never hand-edit. |
| `ledger.json` | the agent (created by `migration_report.py --init`) | per-test status, the new node id, and the ported-symbol map. |
| `MIGRATION_REPORT.md` / `report.json` | `migration_report.py` | the generated report. Never hand-edit. |

## Ledger schema

```json
{
  "schema": 1,
  "tests": [
    {
      "old": "com.testFlows.SmokeTests#navigateThroughTheMenuOptions",
      "status": "verified",
      "new": "tests/ui/test_navigation.py::test_navigate_through_the_menu_options",
      "markers": ["ui", "smoke"],
      "symbols": [
        {
          "old": "com.ui.steps.uicommon.UICommonSteps#openLinkFromHamburgerMenu",
          "new": "ui/pages/hamburger_menu.py::HamburgerMenu.open_link"
        },
        {
          "old": "com.ui.pages.HomePage#clickSearchCatalog",
          "new": "ui/pages/home_page.py::HomePage.click_search_catalog"
        }
      ],
      "notes": "",
      "blocked_reason": null
    }
  ],
  "out_of_scope": [
    {
      "old": "com.testFlows.CommercialRelationTests#validatePublishedMappingInCouchbase",
      "reason": "asserts via Couchbase N1QL over SSH; no equivalent in the pytest framework",
      "approved_by": "user"
    }
  ]
}
```

Rules:

- `old` must match `inventory.json` exactly (`<fqcn>#<method>`); the report lists
  unknown ids as errors.
- `new` is a pytest node id relative to the repo root. Omit the `[param]` part to
  cover every parametrized case of that function; include it to track one case.
- `symbols` is the depth evidence. Add one entry per Java page/step/API/entity
  method the test actually reaches. Format: `<path>::<Class>.<method>` or
  `<path>::<function>`. The report resolves each one against the real file.
- `out_of_scope` needs a `reason` and `approved_by: "user"`. Anything without
  user approval stays `blocked`, which counts against the score.

## Statuses

| Status | Meaning | Counts toward score |
|---|---|---|
| `not_started` | untouched | no |
| `in_progress` | partially ported, cannot run yet | no |
| `code_complete` | fully ported, not yet run green | no |
| `verified` | ported and passing in the recorded run | **yes** |
| `failing` | ported, ran red | no |
| `blocked` | needs a decision or a missing capability (`blocked_reason` required) | no |
| `out_of_scope` | listed in `out_of_scope` with user approval | removed from the denominator |

`--junit` promotes `code_complete`/`failing`/`verified` rows automatically from
the run: a passing node -> `verified`, a failing/error node -> `failing`, a
skipped node -> `blocked` with reason `skipped in run`. Statuses are never
downgraded from `verified` unless the run says the test failed.

## Percentage math

```
total            = len(inventory.tests)
out_of_scope     = len(ledger.out_of_scope)
in_scope         = total - out_of_scope

migration_score  = verified / in_scope * 100          # the headline
code_coverage    = (verified + code_complete) / in_scope * 100
symbol_resolution= resolved_symbols / declared_symbols * 100
gate_pass_rate   = passed_gates / total_gates * 100
```

The headline is deliberately the strictest of these: a test only counts when it
ran green. `code_coverage` shows work that is written but unproven, so a gap
between the two means "run the tests".

`in_scope` shrinks when tests are moved out of scope, which raises the score, so
the report always prints `out_of_scope` next to the headline and lists the
reasons. Report the two numbers together in chat as well.

Per-suite and per-kind breakdowns come from the inventory's `groups` and `kind`
fields, so progress can be read per TestNG group (`SmokeTest`, `regression_5`,
...) without extra bookkeeping.

## Convention gates

Gates are repo-wide static checks. They do not change the headline percentage -
they are reported separately - but a failing gate blocks calling a test done.

| Id | Check | Where |
|---|---|---|
| G1 | no `time.sleep(` | `tests/`, `ui/`, `api/`, `utils/`, `fixtures/` |
| G2 | no raw selectors in tests (`page.locator(`, `page.get_by_`) | `tests/` |
| G3 | no stubs (`TODO`, `FIXME`, `NotImplementedError`, `pass  # stub`) | `tests/`, `ui/`, `api/`, `utils/`, `fixtures/` |
| G4 | every migrated test file has a kind marker (`ui`/`api`/`e2e`) and `@allure.title` | ledger `new` files |
| G5 | no `@pytest.mark.skip` in a migrated test file | ledger `new` files |
| G6 | no `{{...}}` placeholders left in payloads | `data/api_payloads/` |
| G7 | no password in a `parametrize` | `tests/` |
| G8 | no ported factory class (`class *Factory`) | `ui/`, `api/` |

`migration_report.py` prints the offending file and line for each failure. Fix
the code; never relax a gate.

## Worked example

Inventory: 119 tests. The team migrates the `SmokeTest` group (12 tests) and
agrees 3 Couchbase tests are out of scope.

```
in_scope        = 119 - 3 = 116
verified        = 11        (one still red)
code_complete   = 0
failing         = 1
migration_score = 11 / 116 = 9.5%
```

Reported as: `Migration score: 9.5% (11 of 116 in-scope tests verified) ·
out of scope: 3 · failing: 1 · symbol resolution 47/47 · gates 8/8`.

## Report sections

`MIGRATION_REPORT.md` contains, in order: headline, status breakdown, progress
by old TestNG group, progress by kind (ui/api/e2e), symbol resolution with any
unresolved entries, gate results with offending lines, the blocked register with
reasons, the out-of-scope register, and a "next up" suggestion (the group with
the most tests already sharing migrated pages).

## Re-running

The scripts are idempotent. `--init` keeps existing ledger rows and only adds
tests that appeared in a fresh inventory, so re-running after the legacy repo
changes never loses work. If a Java test was deleted upstream, the report lists
it as a stale ledger row instead of silently counting it.
