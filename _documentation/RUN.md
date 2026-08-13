# Run Guide — Tracing & Reports

Quick reference for first-time setup and running tests with Playwright tracing, HTML reports, and Allure.

---

## First-time setup (pip install)

One-time steps before any test run.

### Windows (PowerShell)

```powershell
py --version                          # check the Python launcher
py -m venv .venv                      # create the virtual environment
.\.venv\Scripts\python.exe --version  # verify the venv interpreter
.\.venv\Scripts\Activate.ps1          # activate it
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install
allure --version
```

> Allure reports also need the **Allure CLI** on your PATH (`allure --version`). See [Allure report](#allure-report) if it is missing.

> If activation is blocked:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```



### Windows (Command Prompt)

```bat
py -m venv .venv
.venv\Scripts\python.exe --version
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install
```



### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install
```



### Verify

```bash
pytest --version
playwright --version
allure --version
```

For later sessions, only activate the venv:

```powershell
.\.venv\Scripts\Activate.ps1
```

---



## Output location

All generated artifacts go into a single `reports-results/` folder (gitignored):

```text
reports-results/
├── report.html                    # pytest-html report (self-contained)
├── allure-results/                # Allure raw results (JSON + attachments)
├── videos/<test>/*.webm           # Playwright video recordings (with --video)
└── test-results/<test>/trace.zip  # Playwright traces (with --tracing)
```

`pytest.ini` sets these defaults for **every** run:

```ini
addopts = --html=reports-results/report.html --self-contained-html --alluredir=reports-results/allure-results
```

So a plain `pytest` already writes the HTML report and Allure results into `reports-results/`. Add `--tracing on` to also capture traces. You can still override the paths per run by passing your own `--html=` / `--alluredir=`.

> **Cleaning:** `--clean-alluredir` clears `allure-results` (built into `allure-pytest`). A `pytest_configure` hook in `conftest.py` extends this so the same flag also wipes `reports-results/test-results/` (traces) and `reports-results/videos/`, keeping the whole folder from accumulating stale runs.

---



## Full example (recommended)

Browser + marker + parallel + tracing (HTML + Allure come from the `pytest.ini` defaults above):

```bash
pytest --browser_name chrome -m full -n auto --tracing on
```

Then open the Allure report (see [Allure report](#allure-report)):

```bash
allure serve reports-results/allure-results
```

---



## Run by tag (marker)

Markers are registered in `pytest.ini` (`smoke`, `full`, `ui`, `api`, `e2e`, `regression`).

```bash
# Smoke tests only
pytest -m smoke

# Smoke + headed + tracing
pytest -m smoke --headed --tracing on

# Smoke + browser + parallel
pytest --browser_name chrome -m smoke -n auto --tracing on

# Full suite
pytest -m full

# Everything except smoke
pytest -m "not smoke"
```

Preview which tests a marker selects:

```bash
pytest -m smoke --co -q
pytest -m full --co -q
```

---



## Run one test

By file and test function name. Each test is parametrized per credential, and the case id is the **user key** from `data/input_data/credentials.json` (`user_a`, `user_b`, …), set via `ids=load_credential_ids()`:

```bash
# Single smoke test (first user)
pytest -s "tests/e2e/test_create_order_and_login.py::test_create_order_and_login[user_a]" --headed

# Single smoke test + tracing
pytest -s "tests/e2e/test_create_order_and_login.py::test_create_order_and_login[user_a]" --headed --tracing on

# Second user
pytest -s "tests/e2e/test_create_order_and_login.py::test_create_order_and_login[user_b]" --headed --tracing on

# Single full e2e test
pytest -s "tests/e2e/test_create_order_and_verify_ui.py::test_create_order_and_verify_ui[user_a]" --headed --tracing on
```

By name substring (`-k`):

```bash
pytest -k user_a --headed --tracing on
pytest -k "create_order and user_a" --headed
```

---



## Option reference


| Option                  | Values / example                          | Purpose                                                                                                                                                                                |
| ----------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--browser_name`        | `chromium` (default), `firefox`, `webkit` | Playwright browser type launched by `browser_setup` (default from `config/execution.json`). Branded Google Chrome is selected via `browser_channel` in the config, not by this option. |
| `--url`                 | `http://rahulshettyacademy.com/client`    | App URL (default from `config/execution.json`)                                                                                                                                         |
| `-m`                    | `smoke`, `full`, `"not smoke"`            | Run tests by marker / tag (`pytest.ini`)                                                                                                                                               |
| `-n`                    | `auto`, `3`, `4`                          | Parallel workers (`pytest-xdist`)                                                                                                                                                      |
| `--tracing`             | `on`, `retain-on-failure`                 | Record Playwright traces. `on` keeps every trace; `retain-on-failure` discards the trace of a passing test. A failing test's trace is also attached to the Allure report                |
| `--video`               | `on`, `retain-on-failure`, `off`          | Record a Playwright video per test; attached to the Allure report                                                                                                                      |
| `--html`                | `reports-results/report.html`             | Write HTML report (`pytest-html`); defaulted in `pytest.ini`                                                                                                                           |
| `--self-contained-html` | flag                                      | Embed CSS/JS into `report.html` so it works as one standalone file (no `assets/` folder needed); defaulted in `pytest.ini`                                                             |
| `--alluredir`           | `reports-results/allure-results`          | Write Allure raw results (`allure-pytest`); defaulted in `pytest.ini`                                                                                                                  |
| `--clean-alluredir`     | flag                                      | Clear old results before the run. Clears `allure-results` **and** (via `conftest.py`) the `reports-results/test-results` and `videos` folders, so every clean run starts fresh.        |
| `--headed`              | flag                                      | Show the browser UI (pytest-playwright)                                                                                                                                                |
| `-s`                    | flag                                      | Show print/stdout in the console                                                                                                                                                       |
| `-k`                    | `create`, `"create or order"`             | Run tests matching a name expression                                                                                                                                                   |
| `--co` / `--co -q`      | flag                                      | Collect/list tests without running                                                                                                                                                     |


---



## Tracing

Traces are saved by the `context_setup` fixture to:

```text
reports-results/test-results/<request.node.name>/trace.zip
```

Actual folders from a recent full run (parametrized by user key — `user_a`, `user_b`):

```text
reports-results/test-results/
├── test_create_order_and_verify_ui[user_a]/
│   └── trace.zip
└── test_create_order_and_verify_ui[user_b]/
    └── trace.zip
```

```bash
# Trace every test
pytest --tracing on

# Trace only failing tests
pytest --tracing retain-on-failure
```



### Open / view a trace

After a run with `--tracing on` (or `retain-on-failure`), open the saved `trace.zip` in either of these ways.

#### Option 1 — locally (CLI viewer)

Uses the Playwright trace viewer installed with your venv (no upload). Quote paths that contain `[` / `]` / `@`:

```bash
# Actual traces from the last full run (case id = user key)
playwright show-trace "reports-results/test-results/test_create_order_and_verify_ui[user_a]/trace.zip"
playwright show-trace "reports-results/test-results/test_create_order_and_verify_ui[user_b]/trace.zip"
```

Windows PowerShell:

```powershell
playwright show-trace ".\reports-results\test-results\test_create_order_and_verify_ui[user_a]\trace.zip"
playwright show-trace ".\reports-results\test-results\test_create_order_and_verify_ui[user_b]\trace.zip"
```

This opens a local browser window with the timeline, screenshots, network, and actions.

#### Option 2 — by URL (online viewer)

1. Open: [https://trace.playwright.dev/](https://trace.playwright.dev/)
2. Drag-and-drop a real file from this project, e.g.:
  - `reports-results/test-results/test_create_order_and_verify_ui[user_a]/trace.zip`
  - `reports-results/test-results/test_create_order_and_verify_ui[user_b]/trace.zip`

The file is processed **in your browser** and is **not uploaded** to a server. Useful when you only have the zip and do not want to run the CLI.

---



## Video recording

Playwright records a video of each test's browser context. It's wired into the `context_setup` fixture in `conftest.py` and driven by the `--video` option:

```bash
# Record a video for every test
pytest -m full --video on

# Record, but keep the video only for failing tests
pytest -m full --video retain-on-failure

# Combine with tracing (both attached under the test in Allure)
pytest --browser_name chrome -m full -n auto --tracing on --video on --clean-alluredir
```

- Raw `.webm` files are saved to `reports-results/videos/<test-name>/`.
- Each video is **attached to the Allure report** — open it, expand the test, and the recording appears under the `context_setup` **Tear down** section, in the **UI screenshot/video** group (`video · execution recording`).
- `retain-on-failure` deletes the video for passing tests, so only failures keep one.
- `-n 0` (or `-n auto`) both work; video attaches per test either way.

> Videos are separate from the pytest-html report; view them via Allure (`allure serve reports-results/allure-results`) or directly from `reports-results/videos/`.

---



## HTML report

`pytest.ini` defaults the report to `reports-results/report.html` (self-contained), so a plain `pytest` writes it automatically. Pass `--html=<path>` to override.

### What `--self-contained-html` means

By default, pytest-html writes `report.html` **and** a separate `assets/` folder (CSS/JS). The HTML depends on those files, so if you move or share only `report.html`, styling/scripts can break.

`--self-contained-html` embeds the CSS and JavaScript **inside** `report.html`, so you get a **single file** you can open, email, or copy anywhere without the `assets/` folder. This project enables it by default.


| Flag                                       | Output                    | Best for            |
| ------------------------------------------ | ------------------------- | ------------------- |
| `--html=report.html`                       | `report.html` + `assets/` | Local runs          |
| `--html=report.html --self-contained-html` | one `report.html` only    | Sharing / archiving |


```bash
# Uses the pytest.ini default -> reports-results/report.html (self-contained)
pytest -m smoke

# Override the output path
pytest -m smoke --html=my-report.html --self-contained-html
```

Open `reports-results/report.html` in a browser after the run.

---



## Allure report

> For the full picture — the `allure` Python API, how each layer of the framework is instrumented, project conventions, and troubleshooting — see the [Allure handbook](ALLURE.md).

Two parts are required:

1. **Python plugin** — `allure-pytest` (already in `requirements.txt`)
2. **Allure CLI** — generates/opens the HTML report from `reports-results/allure-results/`



### Install Allure CLI (one-time, if missing)

Check:

```bash
allure --version
```

If missing on Windows (Scoop):

```powershell
scoop install allure
```

Or with Chocolatey:

```powershell
choco install allure-commandline
```

Or download from [Allure releases](https://github.com/allure-framework/allure2/releases) and add the `bin` folder to `PATH`.

### 1) Run tests and collect results

If you see `unrecognized arguments: --alluredir`, install the plugin into the active venv first:

```powershell
pip install -r requirements.txt
# confirm the plugin is loaded (should list allure-pytest):
python -m pytest --version -q
python -m pytest --co -q
```

`--alluredir=reports-results/allure-results` is already set in `pytest.ini`, so any run collects Allure results. Prefer `python -m pytest` so the active venv’s plugins are used. Add `--clean-alluredir` to wipe old results first:

```bash
# Smoke
python -m pytest -m smoke --clean-alluredir

# Full suite + tracing
python -m pytest --browser_name chrome -m full -n auto --tracing on --clean-alluredir

# Single test
python -m pytest -s "tests/e2e/test_create_order_and_login.py::test_create_order_and_login[user_a]" --clean-alluredir
```

Raw JSON results land in `reports-results/allure-results/` (gitignored).

### 2) Open the report

All the ways to open the Allure report:

#### Option A — serve (quickest, temporary)

Builds a report and opens it in your browser on a random local port. Deleted when you stop it (`Ctrl+C`).

```bash
allure serve reports-results/allure-results
```

Pin the host/port (useful for remote/WSL/containers):

```bash
allure serve reports-results/allure-results --host 0.0.0.0 --port 5050
```



#### Option B — generate a static site, then open it

Creates a reusable `reports-results/allure-report/` folder you can reopen or share.

```bash
# 1) build the static report (overwrite any previous one)
allure generate reports-results/allure-results -o reports-results/allure-report --clean

# 2a) open via the Allure CLI (starts a tiny local server)
allure open reports-results/allure-report

# 2b) open on a fixed host/port
allure open reports-results/allure-report --host 0.0.0.0 --port 5050
```



#### Option C — single self-contained HTML file

Generate one portable `index.html` (embeds everything) you can email or archive:

```bash
allure generate reports-results/allure-results -o reports-results/allure-report --clean --single-file
# then open the file directly
start reports-results\allure-report\index.html      # Windows
# open reports-results/allure-report/index.html     # macOS
# xdg-open reports-results/allure-report/index.html # Linux
```

> Note: a non-single-file `allure-report/` must be **served** (via `allure open`) — opening its `index.html` directly with `file://` shows a blank page due to browser security. Use `--single-file` if you want to double-click the HTML.



#### Option D — from your IDE / CI

- **PyCharm / IntelliJ**: install the *Allure* plugin, then right-click `reports-results/allure-results` → open report.
- **VS Code / Cursor**: use the *Allure* extension, or just run `allure serve reports-results/allure-results` in the integrated terminal.
- **CI (Jenkins/GitLab/etc.)**: publish `reports-results/allure-results` and let the Allure plugin/step render the report.


| Command                                                                                   | What it does                                   |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `allure serve reports-results/allure-results`                                             | Temporary local report server (quickest)       |
| `allure serve reports-results/allure-results --port 5050`                                 | Same, on a fixed port                          |
| `allure generate reports-results/allure-results -o reports-results/allure-report --clean` | Writes a reusable `allure-report/` folder      |
| `allure open reports-results/allure-report`                                               | Opens a previously generated report            |
| `allure generate ... --single-file`                                                       | One portable `index.html` you can double-click |




### What the report shows (steps, inputs, locators)

The tests and page objects are instrumented so the report reads like the execution flow, not raw logs:

- **Grouping** — `epic` (E-commerce) → `feature` → `story`, plus `severity` per test.
- **Readable titles** — e.g. `Full E2E order flow · dudued@gmail.com`.
- **Nested steps** with the **locator** and the **input/expected value** inline, for example:
  - `UI · login and open dashboard`
    - `Fill email · locator=#userEmail · input='dudued@gmail.com'`
    - `Fill password · locator=#userPassword · input='***'`
    - `Click login · locator=#login`
  - `UI · verify order confirmation message`
    - `Assert tagline · locator=//p[@class='tagline'] · expected='Thank you for Shopping With Us'`
- **Attachments** — API request payloads, response status, auth token (truncated), and the created order id. Payloads go through `attach_json`, which masks any field whose name looks like a secret (`password`, `token`, `authorization`, …), so a request body cannot leak one.
- **Parameters** — each test is parametrized by **email only**. `allure-pytest` records every parameter's `repr()` and pytest prints the test's arguments in its traceback, so a credentials dict would put the password in the report twice over; the password is resolved inside the test from the `user_passwords` fixture instead.

To add more detail later, use `allure.step(...)` in a page object / util, or `allure.attach(...)` for extra data (screenshots, JSON, etc.). Tests inherit it automatically — no per-test wiring needed.

### Failure artifacts (attached on failure)

When a UI/e2e test fails, the `context_setup` fixture (`fixtures/ui_fixtures.py`) attaches evidence to the Allure **Tear down** section — only for failing tests, so passing runs stay clean. Expand `context_setup::1` and the artifacts are grouped by kind, one collapsible section each:

**Playwright trace**

- **`trace · playwright trace`** — the `trace.zip` itself, so the report is self-contained. Allure cannot render a zip, so this row only offers a download; the next attachment tells you how to open it.
- **`trace · how to open`** — both manual ways to open that exact trace: the ready-to-paste `playwright show-trace "…"` command, and the drag-and-drop route via [trace.playwright.dev](https://trace.playwright.dev/) with the file path to drop. When `TRACE_BASE_URL` is set (CI publishing `reports-results/`), this is replaced by a clickable **`Open Playwright trace`** link plus a `trace · open in viewer` attachment that open the trace in a new tab. See the [Allure handbook](ALLURE.md#opening-a-trace-from-the-report).

**Automation trace code**

- **`traceback · failure trace`** — a readable, Java-style stack trace showing only project frames (built in `conftest.py`, attached via `utils/report.py`).

**UI screenshot/video**

- **`screenshot · failure state`** — full-page PNG of the page at teardown.
- **`video · execution recording`** — the `.webm` recording, when run with `--video on` / `--video retain-on-failure`.

**Browser console/network**

- **`browser console errors`** — browser JS console `error`/`warning` messages plus uncaught page exceptions (`pageerror`). Always attached on failure; shows "No console errors…" when empty.
- **`browser network errors`** — network-level failures (`requestfailed`) and HTTP error responses (`4xx`/`5xx`) seen by the browser page. Always attached on failure; shows "No network failures…" when empty.

A section is only created when it has content, so a run without tracing has no **Playwright trace** group, and a passing test recorded with `--video on` shows **UI screenshot/video** containing only the recording.

API-only tests have no browser page, so their evidence comes from the API layer instead: the `api_context` fixture attaches the same **`traceback · failure trace`**, and `BaseApi` attaches **`response · error body`** (truncated) for any response with status `>= 400`, right inside the failing request's step.

> Console and network logs are captured from the **browser page** only. API calls go through a separate `APIRequestContext` (see `fixtures/api_fixtures.py`) and are not part of them.

### Clean Set up / Tear down (no "Unknown" rows)

pytest logs every fixture finalizer, and Allure renders higher-scope / yield-finalizer wrappers (e.g. `context_setup::<lambda>`) as status-less **"Unknown"** rows, which clutter the report. A `pytest_sessionfinish` hook in `conftest.py` post-processes the Allure `*-container.json` files and removes those status-less setup/teardown entries, keeping only meaningful steps (like the teardown that holds the attachments above).

> **Note on step parameters:** the `@allure.step` *decorator* auto-captures a method's arguments and prints their `repr()` in the report. That produces noise like `playwright = <Playwright object at 0x…>` and can expose secrets (e.g. a password inside a credentials dict). For methods that take the `playwright` object or credentials we use an inline `with allure.step(...)` block instead, which records the step **without** capturing its arguments. The full test is also parametrized by **email only**, so no password ever reaches the report.

---



## Common run recipes

HTML + Allure are written to `reports-results/` by default (see [Output location](#output-location)), so most runs just add `--tracing on`:

```bash
# All tests, default browser/url from config/execution.json
pytest -s

# Smoke only, headed
pytest -m smoke --headed

# Full suite, Firefox, parallel, traces on failure
pytest --browser_name firefox -m full -n auto --tracing retain-on-failure

# Single file
pytest -s tests/e2e/test_create_order_and_login.py --headed --tracing on

# Custom URL
pytest --url http://rahulshettyacademy.com/client -m smoke
```

---



## Preview without running

```bash
pytest --co -q              # list all collected tests
pytest -m smoke --co -q     # preview smoke tests
pytest -m full --co         # preview which tests a marker selects
pytest --markers            # show registered markers
```

---



## Notes

- Parallel runs (`-n`) open multiple browsers at once.
- All artifacts live under `reports-results/` (report.html, allure-results, allure-report, test-results/traces, videos) and the whole folder is gitignored — regenerate it locally after each run.
- `--clean-alluredir` clears `allure-results` **and** `reports-results/test-results` + `videos` (via `conftest.py`), so a clean run leaves no stale artifacts behind.
- HTML report and Allure results paths are defaulted in `pytest.ini` (`addopts`); pass `--html=` / `--alluredir=` to override.
- Defaults for `--browser_name` and `--url` come from `config/execution.json` (loaded via `utils/config_reader.py` in `conftest.py`), which also sets `browser_channel`, `headless`, and `default_timeout_ms`.
- **Browser version:** with `browser_channel: chrome` (the default), tests run the system-installed Google Chrome (auto-updated). Leave `browser_channel` empty to use Playwright's bundled Chromium, whose version is pinned to the installed `playwright` package. See [INSTALL.md → Controlling the browser version](INSTALL.md#controlling-the-browser-version) and the local mapping in `.venv/Lib/site-packages/playwright/driver/package/browsers.json`.
- Test data lives under `data/` — user credentials in `data/input_data/credentials.json` (named keys `user_a`, `user_b`, …, gitignored), loaded via `utils/data_reader.py`. Tests parametrize over `load_credential_emails()` and label each case with the key via `ids=load_credential_ids()`; the password is looked up at run time from the `user_passwords` fixture so it never becomes a report parameter.

