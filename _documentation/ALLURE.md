# Allure Handbook

Everything about Allure in this framework: how it is installed, how results are produced, how the report is opened, the full `allure` Python API, and the exact conventions this project follows.

For general run commands see [RUN.md](RUN.md); for first-time setup see [INSTALL.md](INSTALL.md).

---

## Contents

- [The two parts of Allure](#the-two-parts-of-allure)
- [Install & verify](#install--verify)
- [How results are produced](#how-results-are-produced)
- [Open the report](#open-the-report)
- [The Python API (cheat sheet)](#the-python-api-cheat-sheet)
- [How this project is instrumented](#how-this-project-is-instrumented)
- [Reading a test in the report](#reading-a-test-in-the-report)
- [Failure artifacts](#failure-artifacts)
- [Project conventions](#project-conventions)
- [Recipes](#recipes)
- [Custom hooks in conftest.py](#custom-hooks-in-conftestpy)
- [Optional extras (environment, categories, history, CI)](#optional-extras-environment-categories-history-ci)
- [Filtering runs with Allure options](#filtering-runs-with-allure-options)
- [Command reference](#command-reference)
- [Troubleshooting](#troubleshooting)

---

## The two parts of Allure

Allure is always **two independent pieces**. Mixing them up is the most common source of confusion.

| Part | What it is | How it is installed | What it does |
| ---- | ---------- | ------------------- | ------------ |
| `allure-pytest` (+ `allure-python-commons`) | pytest plugin / the `allure` Python module | pip, already in `requirements.txt` | **Produces** raw results (JSON + attachments) while tests run |
| Allure CLI (`allure`) | Standalone Java-based command-line tool | Scoop / Chocolatey / npm / zip download — **not** pip | **Renders** the raw results into an HTML report |

Consequences worth remembering:

- `pytest` alone produces results even with **no CLI installed** — you just cannot view them yet.
- The CLI needs a **Java runtime (JRE)** on the machine.
- `import allure` in test code comes from `allure-python-commons`; the pytest integration (`--alluredir`, lifecycle, fixture sections) comes from `allure-pytest`.

---

## Install & verify

```bash
pip install -r requirements.txt   # allure-pytest + allure-python-commons
allure --version                  # the CLI (installed separately)
```

If the CLI is missing:

```powershell
scoop install allure              # Windows - Scoop
choco install allure-commandline  # Windows - Chocolatey
npm install -g allure-commandline # any OS with Node.js
```

Or download from [Allure releases](https://github.com/allure-framework/allure2/releases) and add its `bin/` folder to `PATH`.

Confirm the pytest plugin is loaded in the **active venv** (this is what provides `--alluredir`):

```bash
python -m pytest --version    # should list allure-pytest
python -m pytest --co -q      # collection works => plugin args accepted
```

> Prefer `python -m pytest` over bare `pytest` — it guarantees the venv's plugins are used.

---

## How results are produced

`pytest.ini` sets the Allure output directory for **every** run, so no flag is needed:

```1:3:pytest.ini
[pytest]
testpaths = tests
addopts = --html=reports-results/report.html --self-contained-html --alluredir=reports-results/allure-results
```

A plain `pytest` therefore writes:

```text
reports-results/allure-results/
├── <uuid>-result.json      # one per test: name, status, steps, parameters, labels, links
├── <uuid>-container.json   # one per fixture scope: the Set up / Tear down entries
└── <uuid>-attachment.*     # attachment payloads (png, txt, json, webm, ...)
```

Key facts:

- **Results are append-only.** Two runs in a row leave both runs in the folder. Use `--clean-alluredir` to start fresh.
- **`--clean-alluredir` runs at startup**, before tests, and only clears `allure-results`. This project extends it (see [Custom hooks](#custom-hooks-in-conftestpy)) so traces and videos are wiped too.
- **Parallel runs are safe.** Each `pytest-xdist` worker writes its own uniquely named files into the same folder; the report merges them.
- **The whole `reports-results/` folder is gitignored** — it is a build artifact, regenerate it locally.

Typical collection commands:

```bash
# smoke suite, fresh results
python -m pytest -m smoke --clean-alluredir

# full suite: browser, parallel, traces and video, fresh results
python -m pytest --browser_name chrome -m full -n auto --tracing on --video on --clean-alluredir

# one test case (case id = user key from data/credentials/credentials.json)
python -m pytest -s "tests/e2e/test_create_order_and_login.py::test_create_order_and_login[user_a]" --clean-alluredir
```

---

## Open the report

### Option A — `serve` (quickest, temporary)

Builds the report into a temp folder and opens it on a random local port. Gone when you press `Ctrl+C`.

```bash
allure serve reports-results/allure-results
allure serve reports-results/allure-results --host 0.0.0.0 --port 5050   # pinned (remote/WSL/containers)
```

### Option B — `generate` + `open` (reusable)

```bash
allure generate reports-results/allure-results -o reports-results/allure-report --clean
allure open reports-results/allure-report
allure open reports-results/allure-report --host 0.0.0.0 --port 5050
```

### Option C — one portable file

```bash
allure generate reports-results/allure-results -o reports-results/allure-report --clean --single-file
start reports-results\allure-report\index.html        # Windows
# open reports-results/allure-report/index.html       # macOS
# xdg-open reports-results/allure-report/index.html   # Linux
```

> A **non**-`--single-file` report must be **served** (`allure open`). Double-clicking its `index.html` opens it over `file://`, which browsers block from loading the JSON data — you get a blank page. Use `--single-file` when you need to email or archive a report.

### Option D — IDE / CI

- **PyCharm / IntelliJ** — install the *Allure* plugin, right-click `reports-results/allure-results` → open report.
- **VS Code / Cursor** — the *Allure* extension, or just run `allure serve reports-results/allure-results` in the integrated terminal.
- **CI (Jenkins / GitLab / GitHub Actions)** — archive `reports-results/allure-results` as an artifact and let the Allure plugin/step render it; that also gives you the [history trend](#optional-extras-environment-categories-history-ci).

---

## The Python API (cheat sheet)

Everything below comes from `import allure`.

### Steps

```python
# 1) decorator - wraps a whole method, AUTO-CAPTURES its arguments as step parameters
@allure.step("UI · verify order confirmation message")
def verify_order_message(self):
    ...

# 2) decorator with placeholders bound to argument names
@allure.step("Open order {order_id}")
def open_order(self, order_id):
    ...

# 3) context manager - records the step WITHOUT capturing arguments
with allure.step(f"Fill '{self.name}' = '{shown}'"):
    self.locator.fill(value)
```

Steps nest automatically by call depth, so a test step containing a page-object step containing an element step renders as a three-level tree. A step turns **red** when an exception passes through it, which is what makes the failing action obvious in the report.

### Attachments

```python
allure.attach("some text", name="notes", attachment_type=allure.attachment_type.TEXT)
allure.attach(json.dumps(payload, indent=2), name="request · payload", attachment_type=allure.attachment_type.JSON)
allure.attach(page.screenshot(full_page=True), name="screenshot · failure state", attachment_type=allure.attachment_type.PNG)
allure.attach.file("path/to/video.webm", name="video · execution recording", attachment_type=allure.attachment_type.WEBM)
```

Common `attachment_type` values: `TEXT`, `JSON`, `HTML`, `CSV`, `XML`, `PNG`, `JPG`, `SVG`, `WEBM`, `MP4`, `URI_LIST`. An attachment lands **inside whichever step is active**, so attach next to the code it describes.

### Grouping, metadata, links

```python
@allure.epic("E-commerce")                  # top level of the Behaviors tab
@allure.feature("Order creation")           # middle level
@allure.story("Create order via API, ...")  # leaf level
@allure.severity(allure.severity_level.CRITICAL)   # BLOCKER | CRITICAL | NORMAL | MINOR | TRIVIAL
@allure.title("Smoke · create order (API) + login (UI) · {user_credential[userEmail]}")
@allure.description("Longer free-text description shown on the test page.")
@allure.tag("smoke", "checkout")
@allure.link("https://example.com/spec", name="Spec")
@allure.issue("PROJ-123", name="Known bug")
@allure.testcase("TC-42", name="Test case")
def test_something(...):
    ...
```

`@allure.title` supports `{arg}` placeholders — including indexing into a dict, as in `{user_credential[userEmail]}` — which is how each parametrized case gets a readable name.

### Setting metadata at runtime

Use `allure.dynamic.*` when the value is only known while the test runs:

```python
allure.dynamic.title(f"Order {order_id}")
allure.dynamic.description("computed at runtime")
allure.dynamic.feature("Checkout")
allure.dynamic.tag("flaky-env")
allure.dynamic.link("https://tracker/PROJ-9", name="ticket")
```

---

## How this project is instrumented

Reporting is layered: **each layer adds the detail it owns**, and tests inherit all of it without any per-test wiring.

| Layer | File(s) | What it contributes |
| ----- | ------- | ------------------- |
| Test | `tests/**` | `epic` / `feature` / `story` / `severity` / `title`, an `Arrange` step, input attachments |
| Page object | `ui/pages/*.py` | Business-level steps (`UI · login and open dashboard`), assertion steps with locator + expected value |
| Element wrapper | `ui/elements/*.py` | Action substeps with the element's friendly name (`Fill 'Email' = '...'`) and secret masking |
| Component | `ui/components/*.py` | Navigation steps (`Navigate to ORDERS`) |
| API client | `api/base_api.py`, `api/clients/*.py` | HTTP steps (`POST /api/ecom/auth/login`), request payload / response meta / output attachments |
| Fixture | `fixtures/ui_fixtures.py` | Tear-down failure artifacts: screenshot, traceback, console, network, video |
| Hooks | `conftest.py` | Pretty traceback text, extended `--clean-alluredir`, removal of status-less fixture rows |

### Test level

```11:24:tests/e2e/test_create_order_and_login.py
@allure.epic("E-commerce")
@allure.feature("Order creation")
@allure.story("Create order via API, then log in via UI")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Smoke · create order (API) + login (UI) · {user_credential[userEmail]}")
@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.parametrize("user_credential", load_credentials(), ids=load_credential_ids())
def test_create_order_and_login(orders_api: OrdersApi, context_setup, user_credential):
    # read this run's user credentials from the parametrized data
    with allure.step("Arrange · read user credentials"):
        user_email = user_credential["userEmail"]
        user_password = user_credential["UserPassword"]
        allure.attach(user_email, name="input · user email", attachment_type=allure.attachment_type.TEXT)
```

### Element level — friendly names and masking

The element wrappers pair a Playwright `Locator` with a human-readable name, and that name is what appears in the report:

```7:12:ui/elements/text_box.py
class TextBox(BaseElement):
    # replace the field content; mask=True hides secrets (e.g. passwords) in the report
    def fill(self, value: str, mask: bool = False):
        shown = "***" if mask else value
        with allure.step(f"Fill '{self.name}' = '{shown}'"):
            self.locator.fill(value)
```

### Page-object level — locator and expected value inline

```13:17:ui/pages/order_details_page.py
    @allure.step("UI · verify order confirmation message")
    def verify_order_message(self):
        expected_text = load_expected_result("order_confirmation")["tagline"]
        with allure.step(f"Assert tagline · locator=//p[@class='tagline'] · expected='{expected_text}'"):
            expect(self.page.locator("//p[@class='tagline']")).to_have_text(expected_text)
```

### API level — one step per HTTP call, plus payload attachments

`BaseApi` wraps every verb in a step and attaches response metadata, so any client that inherits it is instrumented for free:

```43:50:api/base_api.py
    def post(self, endpoint, data=None, headers=None):
        with allure.step(f"POST {endpoint}"):
            response = self.request_context.post(
                endpoint, data=data, headers=self._default_headers(headers)
            )
            attach_text("response · meta", f"status: {response.status}\nurl: {response.url}")
            log.info("POST %s -> %s", endpoint, response.status)
            return response
```

`api/base_api.py` also exposes two helpers used across the clients:

```python
attach_json("request · login payload", payload)          # pretty-printed JSON attachment
attach_text("output · created order id", order_id)       # plain-text attachment
```

Auth tokens are attached **truncated** (`f"{token[:12]}…"`), never in full.

---

## Reading a test in the report

| Tab / area | What it answers |
| ---------- | --------------- |
| **Overview** | Pass/fail totals, duration, severity split, the failure categories widget |
| **Suites** | Tests grouped as pytest sees them: directory → module → test case |
| **Behaviors** | Tests grouped by `epic` → `feature` → `story` — the business view |
| **Graphs** | Status, severity, duration distribution, retries |
| **Timeline** | When each test ran and on which worker — the quickest way to see parallelism from `-n auto` |
| **Packages** | Tests grouped by Python package path |

Opening a single test gives three sections:

- **Set up** — fixture work before the test (context/page creation, navigation).
- **Test body** — the nested steps from the test, page objects, elements, and API clients.
- **Tear down** — fixture cleanup, and where all [failure artifacts](#failure-artifacts) and the video attachment appear.

A real `test_create_order_and_verify_ui` body reads roughly like this:

```text
Arrange · read user credentials
  input · user email
API · create order
  API · get auth token (user: dudued@gmail.com)
    request · login payload
    POST /api/ecom/auth/login
      response · meta
    output · auth token (truncated)
  request · create-order payload
  POST /api/ecom/order/create-order
    response · meta
  output · created order id
UI · login and open dashboard
  Fill 'Email' = 'dudued@gmail.com'
  Fill 'Password' = '***'
  Click 'Login'
UI · open order history from dashboard
  Navigate to ORDERS
UI · select order from history and open details
  Locate order row · locator=//tbody/tr filter(has_text) · input order_id='...'
  Click View · locator=//td/button[contains(text(), 'View')]
UI · verify order confirmation message
  Assert tagline · locator=//p[@class='tagline'] · expected='Thank you for Shopping With Us'
```

---

## Failure artifacts

When a test fails, the fixture teardowns attach evidence to the **Tear down** section. Passing tests attach nothing except the video, so reports stay clean.

The attachments are not a flat list: each family is wrapped in an `allure.step` inside the teardown, so `context_setup::1` expands into four collapsible groups (Allure shows the count next to each one):

```
Tear down
└── context_setup::1                     4 sub-steps, 6 attachments
    ├── Playwright trace                 trace · playwright trace
    │                                    trace · how to open        (or trace · open in viewer)
    ├── Automation trace code            traceback · failure trace
    ├── UI screenshot/video              screenshot · failure state
    │                                    video · execution recording
    └── Browser console/network          browser console errors
                                         browser network errors
```

A group only appears when it has something in it — no tracing means no **Playwright trace** group, and a passing test run with `--video on` gets **UI screenshot/video** holding just the recording. The `Automation trace code` step lives in `attach_failure_traceback` (`utils/report.py`), so the API fixture produces the same group without ever creating an empty one.

| Attachment | Content | Notes |
| ---------- | ------- | ----- |
| `screenshot · failure state` | Full-page PNG at teardown time | UI/e2e failures only |
| `traceback · failure trace` | Java-style trace with numbered source lines and a `==>` arrow on the failing line | Built by `_format_pretty_trace` in `conftest.py`; only project frames, no `site-packages` noise. Falls back to pytest's raw `longrepr`. Attached for **every** layer — see below |
| `browser console errors` | Browser console `error`/`warning` messages plus uncaught `pageerror` exceptions | Always attached on a UI failure; says "No console errors…" when empty |
| `browser network errors` | `requestfailed` events plus HTTP `4xx`/`5xx` responses | Always attached on a UI failure; says "No network failures…" when empty |
| `trace · playwright trace` | The `trace.zip` itself, so the report is self-contained | Failures only, when tracing is enabled. Allure cannot render a zip, so this row is download-only — the pointer below is how you open it |
| `trace · how to open` / `trace · open in viewer` | Either the local `playwright show-trace "…"` command, or a one-click link into the Playwright viewer | Which one you get depends on `TRACE_BASE_URL` — see [Opening a trace from the report](#opening-a-trace-from-the-report) |
| `video · execution recording` | The `.webm` recording | Needs `--video on` or `--video retain-on-failure`; with `retain-on-failure` the file is deleted for passing tests |
| `response · error body` | Body of any HTTP response with status `>= 400`, truncated at 2000 characters | Attached by `BaseApi` at the moment of the call, inside the request's step |

The traceback is layer-independent: `utils/report.py` owns it, `context_setup` calls it for UI/e2e tests, and `api_context` calls it for API-only tests, which have no browser to screenshot. A guard on the test item means a test using both fixtures attaches it exactly once.

### Opening a trace from the report

Allure has no viewer for a zip file, so the `trace · playwright trace` attachment can only ever show **"Click to download attachment"**. What Allure *can* render as a clickable element is a URL — either in the **Links** block at the top of a test, or inside a `text/uri-list` attachment (both become `<a target="_blank">`).

The catch is that [trace.playwright.dev](https://trace.playwright.dev/) **fetches** the trace from the URL you give it (`?trace=<url>`), so that URL has to be reachable over http(s) with CORS. A local path cannot be linked: browsers refuse to navigate to `file://` from a page, and the viewer could not fetch it either. `attach_trace_pointer` in `utils/report.py` therefore behaves differently depending on whether a published URL exists:

| Situation | What the report shows |
| --------- | --------------------- |
| Local run (no `TRACE_BASE_URL`) | `trace · how to open` — the exact `playwright show-trace "reports-results/test-results/<test>/trace.zip"` command to copy and paste, plus the drag-and-drop route: open [trace.playwright.dev](https://trace.playwright.dev/) and drop that same file on it |
| `TRACE_BASE_URL` is set | `Open Playwright trace` in the **Links** block **and** a `trace · open in viewer` attachment, both opening the viewer in a new tab with the trace already loaded |

Point `TRACE_BASE_URL` at the URL where CI publishes the `reports-results/` folder:

```bash
export TRACE_BASE_URL=https://ci.example.com/job/e2e/42/artifact/reports-results
```

The link is then built as `https://trace.playwright.dev/?trace=$TRACE_BASE_URL/test-results/<test>/trace.zip`, with the test name percent-encoded so parametrized ids like `[user_a]` stay valid.

> Want the one-click link locally too? Serve `reports-results/` over HTTP **with CORS enabled** (`python -m http.server` will not work — it sends no `Access-Control-Allow-Origin`) and set `TRACE_BASE_URL=http://localhost:<port>`. Chrome treats `localhost` as trustworthy, so the https viewer is allowed to fetch from it.

How failure detection works: `pytest_runtest_makereport` in `conftest.py` stores each phase's report on the test item (`rep_setup`, `rep_call`), and `utils/report.py` reads them:

```9:16:utils/report.py
def is_test_failed(node) -> bool:
    """True when this test's setup or call phase failed."""
    return bool(
        (getattr(node, "rep_setup", None) and node.rep_setup.failed)
        or (getattr(node, "rep_call", None) and node.rep_call.failed)
    )
```

Both fixtures gate their artifacts on that one function, so "did this test fail" is answered identically everywhere.

> Console and network logs come from the **browser page** only. Pure API calls go through a separate `APIRequestContext` (`fixtures/api_fixtures.py`) and are captured instead as the `POST/GET …` steps with their `response · meta` and, on an error status, `response · error body` attachments.

---

## Project conventions

Follow these so new tests read like the existing ones.

1. **Every test carries the full label set** — `epic`, `feature`, `story`, `severity`, `title`. Keep `epic` as the product area (`E-commerce`), `feature` as the capability, `story` as the scenario.
2. **`·` (middle dot) separates the layer prefix from the detail.** Prefixes in use: `UI · `, `API · `, `Arrange · `, `input · `, `output · `, `request · `, `response · `, `screenshot · `, `trace · `, `video · `, `traceback · `. The two browser-log attachments are the deliberate exception, named `browser console errors` and `browser network errors` because they read better as plain phrases.
3. **Titles end with the data that identifies the case** — e.g. `… · {user_credential[userEmail]}`. Node ids stay short via `ids=load_credential_ids()` (`[user_a]`, `[user_b]`).
4. **Locators appear in the step text, never in the test.** Tests call page objects; page objects and elements own the selectors and put them into the step (`locator=#userEmail`).
5. **Secrets never reach the report.** There are four independent ways a password can get in, and the framework closes all of them:

| Route into the report | Guard |
| -------------------- | ----- |
| Step text | `TextBox.fill(value, mask=True)` renders `'***'` |
| Attachments | `attach_json` runs every payload through `mask_secrets` in `api/base_api.py`, so any key containing `password`, `token`, `authorization`, `secret`, or `apikey` becomes `"***"` — a client cannot forget to mask. Tokens are additionally truncated |
| The **Parameters** table | Never parametrize over a value that contains a secret (see the next rule) |
| Step parameters | Use `with allure.step(...)`, not the decorator, for methods that receive one (see rule 7) |

6. **Never parametrize a test over a credentials dict.** `allure-pytest` records every pytest parameter as `represent(value)`, and pytest additionally prints the test's arguments in its traceback, so a dict parameter puts the password in **both** the Parameters table and the failure trace — with no way to opt out at the parametrize site. Parametrize over the email (not a secret, and it makes a readable title), keep `ids=` on the user keys for short node ids, and resolve the password from the `user_passwords` fixture inside the test:

```16:21:tests/ui/test_login.py
@pytest.mark.parametrize("user_email", load_credential_emails(), ids=load_credential_ids())
def test_login(context_setup, user_email, user_passwords):
    # resolve this run's password from the fixture. it is deliberately not a test
    # parameter: Allure records every parameter's repr(), so it would reach the report
    with allure.step("Arrange · read user credentials"):
        user_password = user_passwords[user_email]
```

7. **Use `with allure.step(...)` — not the decorator — for any method that receives a secret or a big object.** The decorator captures arguments and prints their `repr()`, which would leak a password from a credentials dict and produce noise like `playwright = <Playwright object at 0x…>`:

```26:32:ui/pages/login_page.py
    # business action: log in and hand back the next page (dashboard).
    # inline step (not @allure.step) so the password argument is not
    # captured as a report parameter
    def login_and_dashboard(self, user_email, user_password) -> DashboardPage:
        with allure.step("UI · login and open dashboard"):
            self.login(user_email, user_password)
            return DashboardPage(self.page)
```

8. **Instrument the layer, not the test.** New reporting detail belongs in an element, page object, API client, or fixture — then every test that uses it benefits.

---

## Recipes

### Add a reporting step to a new page action

```python
# ui/pages/cart_page.py
@allure.step("UI · apply discount code")
def apply_discount(self, code):
    with allure.step(f"Fill discount · locator=#coupon · input='{code}'"):
        self.page.locator("#coupon").fill(code)
```

### Add a new reusable element with report-friendly naming

```python
# ui/elements/link.py
import allure
from ui.elements.base_element import BaseElement

class Link(BaseElement):
    def click(self):
        with allure.step(f"Click link '{self.name}'"):
            self.locator.click()
```

Then, in the page's `__init__`, give it a human name: `self.terms = Link(page.locator("#terms"), "Terms & Conditions")`.

### Attach data mid-test

```python
allure.attach(str(order_id), name="output · order id", attachment_type=allure.attachment_type.TEXT)
allure.attach(json.dumps(body, indent=2), name="response · body", attachment_type=allure.attachment_type.JSON)
```

### Attach a screenshot on purpose (not only on failure)

```python
with allure.step("Evidence · dashboard after login"):
    allure.attach(page.screenshot(full_page=True),
                  name="screenshot · dashboard",
                  attachment_type=allure.attachment_type.PNG)
```

### Mask a secret

```python
self.password.fill(user_password, mask=True)          # renders: Fill 'Password' = '***'
attach_text("output · auth token (truncated)", f"{token[:12]}…")
attach_json("request · login payload", payload)       # secret-looking keys become "***"
```

`attach_json` masks on its own, so the only thing to remember is to use it (rather than a raw `allure.attach`) for request bodies. Add a new hint to `_SECRET_KEY_HINTS` in `api/base_api.py` if your API names a secret field something unusual.

### Link a test to a ticket

```python
@allure.issue("PROJ-123", name="Order total rounding")
def test_order_total(...):
    ...
```

Make the id clickable by giving Allure the URL shape:

```bash
python -m pytest --allure-link-pattern=issue:https://jira.example.com/browse/{}
```

---

## Custom hooks in `conftest.py`

Two project-specific hooks shape the Allure output.

### 1. `--clean-alluredir` also clears traces and videos

`allure-pytest`'s own flag only empties `allure-results`, which would leave stale traces and videos behind. `pytest_configure` extends it:

```54:65:conftest.py
def pytest_configure(config):
    # skip on xdist workers (they have `workerinput`); only the controller cleans,
    # before workers start writing, so we don't delete freshly created results
    if hasattr(config, "workerinput"):
        return
    if not config.getoption("--clean-alluredir", default=False):
        return
    for name in _CLEAN_DIRS:
        target = _RESULTS_ROOT / name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            log.info("cleaned results folder: %s", target)
```

So one flag gives a fully clean `reports-results/`: `allure-results`, `test-results` (traces), and `videos`.

### 2. No "Unknown" rows in Set up / Tear down

pytest reports every fixture finalizer, and Allure renders higher-scope or yield-finalizer wrappers (e.g. `context_setup::<lambda>`) as status-less **"Unknown"** rows. A `pytest_sessionfinish` hook post-processes the raw `*-container.json` files and drops any `befores`/`afters` entry whose status is not one of `passed`, `failed`, `broken`, `skipped`:

```97:107:conftest.py
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    config = session.config
    # only the xdist controller post-processes, after all workers have flushed results
    if hasattr(config, "workerinput"):
        return
    alluredir = config.getoption("--alluredir", default=None)
    if not alluredir:
        return
    for container_path in Path(alluredir).glob("*-container.json"):
        _strip_unknown_fixture_steps(container_path)
```

Both hooks are xdist-aware: only the controller process runs them, so worker results are never deleted or half-processed.

---

## Optional extras (environment, categories, history, CI)

None of these are configured in the repo today — this is how to add them when needed. All of them work by dropping files into `reports-results/allure-results/` **before** `allure generate` / `allure serve`.

### Environment widget

Create `reports-results/allure-results/environment.properties`:

```properties
Browser=chrome
Browser.Channel=chrome
URL=http://rahulshettyacademy.com/client
Headless=false
Python=3.12.4
Playwright=1.55.0
```

A natural home for generating this is a session fixture or `pytest_sessionfinish`, reading the values from `execution_config`.

### Failure categories

Create `reports-results/allure-results/categories.json` to bucket failures on the Overview page:

```json
[
  {
    "name": "Timeouts",
    "matchedStatuses": ["broken", "failed"],
    "messageRegex": ".*TimeoutError.*"
  },
  {
    "name": "Assertion failures",
    "matchedStatuses": ["failed"],
    "messageRegex": ".*AssertionError.*"
  }
]
```

### History and trends

Trend widgets need the previous report's history carried into the new results:

```bash
# after a previous `allure generate` into reports-results/allure-report
cp -r reports-results/allure-report/history reports-results/allure-results/history
allure generate reports-results/allure-results -o reports-results/allure-report --clean
```

PowerShell:

```powershell
Copy-Item -Recurse -Force reports-results\allure-report\history reports-results\allure-results\history
```

In CI, the Allure plugin normally handles this automatically.

### CI executor link

`reports-results/allure-results/executor.json` labels the report with the build that produced it:

```json
{
  "name": "Jenkins",
  "type": "jenkins",
  "buildName": "pytest-playwright #42",
  "buildUrl": "https://jenkins.example.com/job/pytest-playwright/42/",
  "reportUrl": "https://jenkins.example.com/job/pytest-playwright/42/allure/"
}
```

CI outline: run `python -m pytest ... --clean-alluredir`, archive `reports-results/allure-results`, then let the CI Allure plugin/step generate and publish the report.

---

## Filtering runs with Allure options

`allure-pytest` can select tests by their Allure labels instead of pytest markers — handy when the taxonomy is what you care about:

```bash
python -m pytest --allure-severities=critical,blocker
python -m pytest --allure-epics="E-commerce"
python -m pytest --allure-features="Order creation"
python -m pytest --allure-stories="User can log in via the UI"
python -m pytest --allure-ids=TC-42,TC-43          # tests carrying @allure.id / testcase ids
python -m pytest --allure-label=owner=qa-team      # any custom label, as name=value
python -m pytest --allure-link-pattern=issue:https://jira.example.com/browse/{}
```

Markers (`-m smoke`) and Allure filters can be combined; they narrow the selection independently.

One more plugin option worth knowing: `allure-pytest` attaches pytest's captured **log / stdout / stderr** to each test automatically. Since `pytest.ini` streams logs live (`log_cli = true`), the report gets the same content as a `log` attachment. Pass `--allure-no-capture` to suppress those attachments when they are just noise.

---

## Command reference

| Command | What it does |
| ------- | ------------ |
| `python -m pytest` | Collects Allure results into `reports-results/allure-results` (default from `pytest.ini`) |
| `python -m pytest --clean-alluredir` | Same, after wiping `allure-results` + `test-results` + `videos` |
| `python -m pytest --alluredir=<dir>` | Override the results directory |
| `allure --version` | Verify the CLI (and its Java runtime) is available |
| `allure serve reports-results/allure-results` | Temporary report server (quickest) |
| `allure serve reports-results/allure-results --port 5050` | Same, on a fixed port |
| `allure generate reports-results/allure-results -o reports-results/allure-report --clean` | Build a reusable report folder |
| `allure open reports-results/allure-report` | Serve a previously generated report |
| `allure generate ... --single-file` | One portable `index.html` you can double-click or email |

---

## Troubleshooting

| Symptom | Cause | Fix |
| ------- | ----- | --- |
| `unrecognized arguments: --alluredir` | `allure-pytest` not installed in the active interpreter | `pip install -r requirements.txt`, then run via `python -m pytest` |
| `allure : command not found` / not recognized | CLI not installed or not on `PATH` | See [Install & verify](#install--verify) |
| `allure` fails mentioning Java / `JAVA_HOME` | No JRE available | Install a JRE (the CLI is a Java app) |
| Report opens blank from `file://` | Non-`--single-file` report opened directly | Use `allure open`, or regenerate with `--single-file` |
| Report shows tests from previous runs | Results directory is append-only | Add `--clean-alluredir` |
| "No results found" / empty report | Wrong directory, or tests never ran | Point at `reports-results/allure-results`; confirm the folder has `*-result.json` files |
| `import allure` fails | `allure-python-commons` missing | `pip install -r requirements.txt` |
| Password or object `repr` visible in a step | `@allure.step` decorator captured the arguments | Switch that method to `with allure.step(...)`, and mask secrets |
| "Unknown" rows in Set up / Tear down | The post-processing hook did not run | It needs `--alluredir` (default) and the controller process; check the `pytest_sessionfinish` hook in `conftest.py` |
| No video in the report | Video recording not requested | Run with `--video on` (or `retain-on-failure`, which keeps it only for failures) |
| Attachment lands under the wrong step | `allure.attach` attaches to the **currently open** step | Move the call inside the intended `with allure.step(...)` block |
