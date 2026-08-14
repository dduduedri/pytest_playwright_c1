# Installation Guide

First-time setup for the **pytest + Playwright** framework.

## Prerequisites

- Python 3.9 or newer — check with `py --version` (Windows) or `python3 --version` (macOS/Linux)
- Git

## 1. Clone the repository

```bash
git clone <repository-url>
cd pytest_playwright
```

## 2. Create and activate a virtual environment

### Windows (PowerShell)

Use the `py` launcher to create the venv, verify the interpreter, then activate:

```powershell
# check the Python launcher
py --version

# create the virtual environment named .venv
py -m venv .venv

# verify the venv interpreter works
.\.venv\Scripts\python.exe --version

# activate it
.\.venv\Scripts\Activate.ps1
```

> If activation is blocked, allow scripts for the current user once:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

> Prefer not to rely on activation? Prefix commands with the venv interpreter, e.g.
> `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

### Windows (Command Prompt)

```bat
py -m venv .venv
.venv\Scripts\python.exe --version
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
```

## 3. Upgrade pip

After activation, `python` / `pip` point at the venv:

```bash
python -m pip install --upgrade pip
```

## 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 5. Install Playwright browsers

This downloads the browser binaries required by Playwright:

```bash
playwright install
```

To install only a specific browser (optional):

```bash
playwright install chromium
```

### Controlling the browser version

There are two separate mechanisms, depending on whether you use Playwright's bundled
Chromium or the real Google Chrome:

**a) Bundled Chromium — version is tied to the Playwright package version.**
`playwright install chromium` downloads the Chromium build pinned to your installed
`playwright` version. To change the Chromium version, change the Playwright version:

```bash
pip install playwright==1.55.0     # each release pins a specific Chromium build
playwright install chromium
```

See the exact version for your install in either of these ways:

- Local mapping file: `.venv/Lib/site-packages/playwright/driver/package/browsers.json`
  (look at the `chromium` entry's `browserVersion`).
- Preview what would be installed: `py -m playwright install --dry-run chromium`.
- Playwright release notes: <https://playwright.dev/python/docs/release-notes>
  (or the source `browsers.json`:
  <https://github.com/microsoft/playwright/blob/main/packages/playwright-core/browsers.json>).

**b) Branded channel — version follows the browser installed on the machine.**
Set `"browser_channel"` in `config/execution.json` to launch a **system-installed**
browser (auto-updated by its vendor) instead of the bundled Chromium. Install/select a
channel with:

```bash
playwright install chrome          # Google Chrome (stable), system-wide
playwright install msedge          # Microsoft Edge
playwright install chrome-beta     # a newer Chrome build
```

Valid channels: `chrome`, `chrome-beta`, `chrome-dev`, `chrome-canary`, `msedge`,
`msedge-beta`, `msedge-dev`. To pin a specific Chrome version, install that channel's
browser and set the matching value in `config/execution.json` (e.g. `chrome-beta`).

> The default config ships `"browser_channel": null`, so `playwright install` is all you
> need. If you set it to `chrome`, make sure Google Chrome is available on the machine —
> either already installed, or via `playwright install chrome`.

## 6. Install the Allure CLI (optional, for viewing reports)

Allure has **two separate parts**:

1. **`allure-pytest`** — the Python plugin that *produces* the raw results
   (`reports-results/allure-results/`). It is already in `requirements.txt`, so
   step 4 (`pip install -r requirements.txt`) covers it. No extra action needed.
2. **Allure CLI** — the standalone `allure` command that *renders* the report
   (`allure serve` / `generate` / `open`). It is **not** a pip package and must be
   installed separately. It also requires **Java (a JRE)** to run.

You only need the CLI to *view* the report. Running `pytest` still generates the raw
results without it.

Check whether the CLI is already installed:

```bash
allure --version
```

If it is missing, install it:

```powershell
# Windows - Scoop
scoop install allure

# Windows - Chocolatey
choco install allure-commandline

# Any OS with Node.js
npm install -g allure-commandline
```

Or download from [Allure releases](https://github.com/allure-framework/allure2/releases)
and add its `bin/` folder to your `PATH`.

> Note: the CLI is a Java application, so it also needs a JRE. For everything about
> Allure in this project, see the [Allure handbook](ALLURE.md).

## 7. Verify the installation

```bash
pytest --version
playwright --version
allure --version      # only if you installed the Allure CLI in step 6
```

## 8. Point the framework at your application

Two files decide what gets tested:

- `config/environment.json` — one entry per environment, keyed by environment name, each
  with the required `ui` and `apiHost` URLs plus the optional `keycloakUrl`, `a3sUrl` and
  `posUrl` services. `config/execution.json` holds the run behaviour instead: which
  `environment` to use (only needed when the file defines more than one), browser,
  channel, headless, default timeout, `test_id_attribute` and `ignore_https_errors`.
- `data/input_data/credentials.json` — create it with your real accounts, as
  `{"default": {"user": "...", "password": "..."}}`. It is git-ignored and never
  committed, so every machine and CI runner provides its own.

The three example tests are skipped until their page object / API client points at your
app — see [Point the template at your application](../README.md#point-the-template-at-your-application).

## 9. Run the tests

```bash
pytest -s
```

Run in headed mode (visible browser):

```bash
pytest -s --headed
```

Run against a specific browser:

```bash
pytest -s --headed --browser_name firefox
```

Run in parallel across CPU cores (via `pytest-xdist`):

```bash
pytest -n auto   # one worker per CPU core
pytest -n 3      # use a specific number of workers
```

Generate an HTML report (via `pytest-html`):

```bash
pytest --html=report.html --self-contained-html
```

Record a Playwright trace (saved to `reports-results/test-results/<test-name>/trace.zip`):

```bash
pytest --tracing on
```

Combined example (browser, marker, parallel, tracing, HTML report):

```bash
pytest --browser_name chromium -m e2e -n auto --tracing on --html=report.html
```

View a trace locally, or open [trace.playwright.dev](https://trace.playwright.dev/) and
drag-and-drop the `trace.zip` onto the page:

```bash
playwright show-trace "reports-results/test-results/<test-name>/trace.zip"
```

## 10. Deactivate the virtual environment

When you are finished working:

```bash
deactivate
```
