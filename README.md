# Playwright + pytest Automation Framework — Template

A product-agnostic starting point for UI, API and end-to-end test automation in Python.
Nothing in it is tied to a particular application: you point it at your own app, replace
the example page object and API client, and start writing tests.

What comes ready to use:

- **Playwright + pytest** with a session-scoped browser and a fresh context per test.
- **Page objects and reusable elements** (`Button`, `TextBox`, `Checkbox`, `Dropdown`) that
  report themselves into Allure with human-readable names and mask secrets.
- **API clients** over Playwright's `APIRequestContext`, with request/response evidence
  attached automatically and secret-looking fields redacted.
- **Allure reporting** with grouped failure artifacts: Playwright trace, readable
  traceback, screenshot, video, browser console and network errors.
- **External configuration and test data** — no URLs, credentials or payloads in code.

---

## Structure

```text
pytest_playwright_c1/
├── ui/
│   ├── pages/            base_page.py + login_page.py (EXAMPLE page object)
│   ├── elements/         reusable element wrappers: button, text_box, checkbox, dropdown
│   └── components/       page sections shared by several pages (add yours here)
├── api/
│   ├── base_api.py       HTTP verbs + Allure attachments + secret masking
│   ├── clients/          one client per business resource (auth_api.py is the EXAMPLE)
│   └── models/           optional typed payload models
├── tests/
│   ├── ui/               browser-only tests
│   ├── api/              no-browser tests
│   └── e2e/              API setup + UI verification
├── config/
│   ├── environment.json  WHERE the run points: one entry per environment
│   └── execution.json    HOW the run behaves: environment, browser, headless, timeout
├── data/
│   ├── input_data/       concrete values (credentials.json, git-ignored)
│   ├── api_payloads/     request-body templates with <placeholders>
│   └── expected_results/ values assertions compare against
├── fixtures/             ui_fixtures.py, api_fixtures.py, data_fixtures.py
├── utils/                config_reader, data_reader, logger, report
├── conftest.py           CLI options + Allure/reporting hooks
├── pytest.ini            testpaths, markers, report output, live logs
└── _documentation/       INSTALL.md, RUN.md, ALLURE.md, CURSOR.md
```

---

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install
python -m pytest
```

A fresh clone runs green: the three example tests are skipped until you point them at
your application. Full setup details are in [INSTALL.md](_documentation/INSTALL.md),
and [quick-run.md](quick-run.md) is the shortest path to a first run with a trace.

---

## Point the template at your application

1. **Set the URLs.** `config/environment.json` is the only place the target application
   is named. It holds one entry per environment, keyed by environment name, so several
   environments can live side by side:

   ```json
   {
     "my-env": {
       "ui": "https://my-app.example.com",
       "apiHost": "https://api.example.com",
       "keycloakUrl": "https://keycloak.example.com/auth/realms/my-env"
     }
   }
   ```

   `ui` and `apiHost` are required; `keycloakUrl`, `a3sUrl` and `posUrl` are optional
   extra services. Pick the environment per run with `pytest --env my-env`; without the
   flag, `"environment"` in `config/execution.json` decides (and a file with a single
   entry needs neither).

   `config/execution.json` also controls how the run behaves: `browser`,
   `browser_channel` (set it to `"chrome"` only if you need branded Chrome), `headless`,
   `default_timeout_ms`, `test_id_attribute` (the attribute `get_by_test_id()` reads —
   Playwright's default is `data-testid`) and `ignore_https_errors` (needed for an
   environment served with a self-signed or internal certificate). Any run can override
   these with `--env`, `--url`, `--browser_name`, `--headed` / `--headless`.

2. **Add your users.** Create `data/input_data/credentials.json` with your real accounts.
   That file is git-ignored and never committed, so each machine (and CI) provides its
   own:

   ```json
   {
     "default": { "user": "my_user", "password": "change-me" }
   }
   ```

   The key becomes the pytest case id, so keep it short. `default` is the account the
   `logged_in_page` fixture signs in with; add more keys (`editor`, `reader`, …) for
   tests that need another role.

3. **Rewrite the example page object.** `ui/pages/login_page.py` is the reference for
   every page you add: locators in `__init__` wrapped as reusable elements, business
   methods that describe intent, and a verification method that reads its expected value
   from `data/expected_results/`. Point its three locators at your real login form, then
   add one file per page. When a page leads to another, return that page object so tests
   read as a chain.

4. **Rewrite the example API client.** `api/clients/auth_api.py` shows the pattern:
   one class per business resource, `LOGIN_ENDPOINT` at the top, the request body loaded
   from `data/api_payloads/login.json` with `<placeholders>` substituted at the call site.
   Add a fixture for each new client in `fixtures/api_fixtures.py`.

5. **Rewrite the example tests and drop the skip markers.** Each of the three tests
   carries `@pytest.mark.skip(reason="Template example …")`. Remove that marker once the
   page object / API client behind it points at your app, and rename the Allure `epic`
   from `Example` to your product area.

6. **Delete what you do not need.** The example files exist to be replaced — a template
   with a stale example is worse than an empty folder.

### Migrating from another framework

Work layer by layer rather than test by test:

| Bring over | Where it goes |
| ---------- | ------------- |
| Selectors / locators | Into the page object or component that owns them — never into a test, and never into a separate `locators/` module |
| Login and navigation helpers | Business methods on page objects; shared sections (header, nav, dialogs) become `ui/components/` |
| Waits and retries | Delete them: Playwright auto-waits, and `expect()` retries assertions |
| HTTP calls | A client per resource under `api/clients/`, inheriting `BaseApi` for steps and evidence |
| Hard-coded test data | `data/input_data/` (values), `data/api_payloads/` (body shapes), `data/expected_results/` (expected values) |
| Environment/URL switches | `config/environment.json` (target app) and `config/execution.json` (run behaviour), both read through `utils/config_reader.py` |
| Setup/teardown classes | pytest fixtures in `fixtures/` |
| Custom screenshot/log-on-failure code | Nothing to do: `context_setup` already attaches trace, traceback, screenshot, video, console and network evidence on failure |

Coming from the Java/TestNG Playwright framework specifically? Use the
`migrate-java-tests-to-pytest` skill in `.cursor/skills/`: it carries the
class-by-class translation tables, a per-test ledger, convention gates, and a
generated `migration/MIGRATION_REPORT.md` with the percentage migrated.

---

## The example tests

| Test | What it demonstrates |
| ---- | -------------------- |
| `tests/ui/test_login.py` | A browser-only test driven entirely through a page object, parametrized over the users in the credentials file |
| `tests/api/test_auth_api.py` | A no-browser test calling a domain API client |
| `tests/e2e/test_api_login_then_ui_login.py` | The e2e shape: API does the fast setup, the UI verifies only what needs a browser |

All three parametrize over the user **email** and resolve the password from the
`user_passwords` fixture, because Allure records every test parameter — that is the
convention to copy, not just an implementation detail.

---

## Running tests

```bash
python -m pytest                     # everything (markers: ui, api, e2e, smoke, full, regression)
python -m pytest -m ui --headed      # one marker, visible browser
python -m pytest -n auto             # parallel
python -m pytest --tracing retain-on-failure --video retain-on-failure
```

Reports and artifacts land under `reports-results/`. See [RUN.md](_documentation/RUN.md)
for every option, tracing and video modes, and how to open a trace;
[ALLURE.md](_documentation/ALLURE.md) for the report itself, the failure artifacts and the
reporting conventions; [CURSOR.md](_documentation/CURSOR.md) for running inside Cursor.

---

## Conventions worth keeping

1. Tests stay thin: no selectors, no config reading, no credential file access.
2. Locators live with the page or component that uses them.
3. Element wrappers exist to add reporting, masking or shared waiting — not to rename
   Playwright methods.
4. Business steps go on page and client methods; technical steps on elements.
5. Secrets never reach the report: `mask=True` on inputs, `attach_json` for payloads,
   and never parametrize over a value that contains one.
6. No `time.sleep()`; use Playwright's waiting and `expect()`.
7. Add a new layer (`flows/`, `factories/`, `schemas/`) only when repetition justifies it.

The full ruleset lives in `.cursor/skills/playwright-pytest-automation-framework/SKILL.md`,
which is also what guides Cursor's agent when it writes code in this repo.
