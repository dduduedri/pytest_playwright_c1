---
name: migrate-java-tests-to-pytest
description: >
  Migrates tests from the legacy Java/TestNG/Maven Playwright framework
  (c1-playwright-automation-old-framework) into this Python pytest + Playwright
  template, and generates a migration report with the percentage of tests
  migrated successfully. Use when migrating, porting, or converting Java/TestNG
  tests, page objects, step classes, API steps, entities, payloads or
  configuration into the pytest framework, or when the user asks for migration
  status, coverage, or a migration percentage.
version: 1.0.0
---

# Migrate Java/TestNG tests into this pytest template

The source framework is Java + TestNG + Maven + REST Assured (default path:
`c1-playwright-automation-old-framework/`). The target is this repository.
Migration is **per test**, bottom-up, and every migrated test must run green
before it counts.

Always obey the target framework's own rules in
`.cursor/skills/playwright-pytest-automation-framework/SKILL.md`. This skill
only adds the translation and bookkeeping on top of it.

## Definition of done

100% means: **every in-scope Java `@Test` method has a pytest test that runs
green**, with everything it touches really implemented. Tests that cannot move
(Couchbase/SSH/OCP/Nexus/thread-report/etc.) go to the out-of-scope register
with a reason, and the user confirms that list. Nothing else may be dropped.

## Workflow

Copy this checklist into the conversation and keep it updated:

```
Migration progress:
- [ ] Phase 0: baseline inventory
- [ ] Phase 1: one-time target setup
- [ ] Phase 2: pick the slice
- [ ] Phase 3: trace each Java test to the bottom
- [ ] Phase 4: move config + data
- [ ] Phase 5: build bottom-up (elements -> pages -> flows / api clients)
- [ ] Phase 6: write the pytest tests
- [ ] Phase 7: gates
- [ ] Phase 8: run green
- [ ] Phase 9: ledger + report
```

### Phase 0 - baseline inventory

```bash
python .cursor/skills/migrate-java-tests-to-pytest/scripts/inventory_old_framework.py
python .cursor/skills/migrate-java-tests-to-pytest/scripts/migration_report.py --init
```

Writes `migration/inventory.json` (every Java `@Test`, its groups, description,
kind and best-effort call list, plus layer counts) and `migration/ledger.json`
(one row per Java test, all `not_started`). The inventory is the denominator of
every percentage, so never hand-edit it - re-run the script instead.

### Phase 1 - one-time target setup

Done once, before the first test. **All five are already in the target** - check them
instead of rebuilding them, and extend only what a new slice needs:

1. `pytest.ini`: the markers the migrated suite needs (`ui`, `api`, `e2e`, `smoke`,
   `regression`; add `sanity` when the first `sanity` slice lands).
2. The test-id attribute the legacy UI uses: `execution.json: test_id_attribute`
   (`data-test-id`), applied by `playwright.selectors.set_test_id_attribute(...)` in
   `browser_setup`, so `get_by_test_id()` works against the app. `ignore_https_errors`
   lives next to it, and the OCP environments need it.
3. `config/environment.json`: one entry per environment keyed by `env_name`, keeping the
   Java key names (`ui`, `apiHost`, `keycloakUrl`, `a3sUrl`, `posUrl`);
   `execution.json: environment` selects one. `utils/config_reader.py` maps them to
   `application_url`, `api_url`, `keycloak_url`, `asm_url`, `pos_url`.
4. `utils/test_data.py`: `unique_name(prefix)` (timestamp + short random suffix; the Java
   `TestDataGenerator` is timestamp-only and collides under `-n`). Add the other
   generators when a slice needs them.
5. The `logged_in_page` fixture, because Java logs in for every test in `@BeforeMethod`:
   it signs in through `KeycloakLoginPage` with the `default` user from
   `credentials.json` and waits for the app shell. UI tests depend on it instead of
   repeating login.

### Phase 2 - pick the slice

Migrate one TestNG group at a time (`SmokeTest` first, then `sanity`, then the
`regression_*` shards), because a group shares pages and steps, so each next
test gets cheaper. Never start a second group while the first has red tests.

### Phase 3 - trace each Java test to the bottom

For every test in the slice, read the Java method body and follow **every**
call: test -> `*Steps` -> page -> element, and test -> `apiStepFactory()` /
entity -> `ApiExecutor` -> payload JSON. List the leaf symbols before writing
Python. `migration/inventory.json` has a best-effort `calls` list per test -
treat it as a hint, not as the truth.

Do not skip a branch because it looks incidental. A migrated test that reaches
a stub is **not** migrated.

### Phase 4 - move config + data

Java config keys -> `config/environment.json` / `config/execution.json`,
`users/users.yaml` -> `data/input_data/credentials.json`,
`src/main/resources/payloads/**` -> `data/api_payloads/**` with `{{token}}`
rewritten to `<token>`, and the `com/data/**` enums/constants the slice needs ->
JSON under `data/input_data/`. Full key-by-key tables:
[references/java-to-python-mapping.md](references/java-to-python-mapping.md).

Copy string literals **exactly** (labels, statuses, validation messages, even
leading spaces) - the legacy values are asserted against a live app.

### Phase 5 - build bottom-up

Order: element wrappers -> page objects -> flows (only if a business action
spans pages) -> API clients. For each layer:

- **Elements**: `ui/elements/` already has Button, TextBox, Checkbox, Dropdown.
  Add Link, RadioButton, ToggleButton, DatePicker, Collapsible, VerticalDots
  only when a migrated page needs them, following the existing element style
  (`BaseElement(locator, name)` + Allure substep).
- **Pages**: one Python page object per Java page/panel class. Locators live in
  `__init__`, business actions above, `verify_*` methods for assertions.
- **Steps**: the Java `steps/` layer does **not** survive as a layer. A step
  method that drives one page becomes a method on that page object; a step
  method that orchestrates several pages becomes a function in `ui/flows/`.
  Never port `PageFactory` / `StepFactory` - pytest fixtures and direct
  construction replace them.
- **API**: `ApiExecutor` + Postman envelope + entity classes become
  `api/clients/<domain>_api.py` on top of `BaseApi`, with the request body as a
  payload template. Keep an entity-style object only when tests genuinely chain
  off it (`api/models/`), holding an id plus its client.

### Phase 6 - gates

Run the report script's gates before claiming a test is done:

```bash
python .cursor/skills/migrate-java-tests-to-pytest/scripts/migration_report.py
```

It fails on: `time.sleep`, raw selectors in tests, `TODO`/`NotImplementedError`
stubs, a migrated test without a kind marker or `@allure.title`, a migrated test
still carrying `@pytest.mark.skip`, `{{...}}` left in a payload, a password in
`parametrize`, and any ported `*Factory` class. Fix the code, not the gate.

### Phase 7 - run green

```bash
pytest tests/ui/test_navigation.py::test_navigate_through_the_menu_options --headed
pytest -m smoke --junitxml=reports-results/junit.xml
```

A test counts as migrated only when it passes against the real application. If
it fails for an environment reason (app down, missing data), say so explicitly -
do not mark it verified.

### Phase 8 - ledger

Record the result in `migration/ledger.json`: `status`, the new node id, the
markers, and the `symbols` map (each Java symbol you ported -> its Python
target, e.g. `ui/pages/home_page.py::HomePage.click_create_br`). The symbol map
is what proves the test was migrated in depth rather than faked, and the report
resolves every entry against the real files.

Schema, statuses and rules: [references/scoring-and-ledger.md](references/scoring-and-ledger.md).

### Phase 9 - report

```bash
pytest -m smoke --junitxml=reports-results/junit.xml
python .cursor/skills/migrate-java-tests-to-pytest/scripts/migration_report.py --junit reports-results/junit.xml
```

`--junit` flips ledger rows to `verified`/`failing` from the actual run, so the
headline number is evidence-based. The script writes
`migration/MIGRATION_REPORT.md` + `migration/report.json` and prints the
headline. Always show the user the headline plus the breakdown table, and name
the top blockers.

## The percentage

```
in_scope        = total Java @Test methods - out_of_scope
migration score = verified / in_scope * 100     <- the headline
```

Reported next to it, because a single number hides the truth:

| Metric | Meaning |
|---|---|
| Verified | migrated and passing in the recorded run |
| Code complete | ported, not yet run green |
| Failing | ported, ran red |
| Blocked | needs a decision or missing capability |
| Not started | untouched |
| Symbol resolution | ledger symbols that resolve to real Python code |
| Gate pass rate | convention gates passing |
| Out of scope | agreed not migrated, with reasons |

Never present the score without the out-of-scope count next to it: dropping
tests raises the percentage, and the user must see that trade-off.

## Non-negotiables

1. **No stubs.** No `TODO`, no `NotImplementedError`, no empty method on a path
   a migrated test executes.
2. **No `time.sleep`.** `WaitUtils.retry(() -> assertThat(...))` becomes a
   Playwright web-first assertion (`expect(...).to_be_visible()`), not a Python
   retry loop.
3. **Exact string literals** from the Java data classes.
4. **No new abstraction layers** beyond the target framework's structure; no
   factories, no locator packages, no step class that only delegates.
5. **Secrets stay out of the report**: never parametrize a password, never put
   one in a step name (`TextBox.fill(value, mask=True)`).
6. **Preserve traceability**: the Java group becomes a marker and/or
   `@allure.tag`, and the ticket id from `@Test(description=...)` becomes
   `@allure.title` text plus `@allure.issue`/`@allure.link`.
7. **Blanket retries do not come along.** `retryAnalyzer = RetryAnalyzer.class`
   is not ported per test; if the team wants parity, run CI with
   `--reruns` (pytest-rerunfailures) and say so once.
8. **One test at a time, green before next.** Bulk-converting many tests
   without running them produces a high "code complete" and a low score.

## Report template

`migration/MIGRATION_REPORT.md` is generated, but keep this shape when
summarizing in chat:

```markdown
Migration score: 34.5% (41 of 119 in-scope tests verified)
Out of scope: 7 tests (Couchbase/SSH) - awaiting sign-off

| Status | Tests |
|---|---|
| Verified | 41 |
| Code complete | 6 |
| Failing | 2 |
| Blocked | 3 |
| Not started | 67 |

Symbol resolution: 312/318 (98.1%) · Gates: 8/8
Top blockers: <reason> (n tests), ...
Next up: <group> (n tests, shares pages already migrated)
```

## Scripts

| Script | Use |
|---|---|
| `scripts/inventory_old_framework.py` | Execute. Scans the Java repo, writes `migration/inventory.json`. Re-run after the legacy repo changes. |
| `scripts/migration_report.py --init` | Execute once. Creates `migration/ledger.json` from the inventory (idempotent: keeps existing rows). |
| `scripts/migration_report.py [--junit path]` | Execute. Runs gates, resolves symbols, writes the report, prints the headline. |

Both are stdlib-only and take `--old-root` / `--repo-root` if the paths differ.

## References

- [references/java-to-python-mapping.md](references/java-to-python-mapping.md) -
  per-layer translation tables: TestNG to pytest, elements, pages, steps, API,
  Allure, config keys, data/enums, waits.
- [references/scoring-and-ledger.md](references/scoring-and-ledger.md) -
  ledger schema, statuses, gate list, percentage math, worked example.
