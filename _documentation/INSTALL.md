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
This project uses `"browser_channel": "chrome"` in `config/execution.json`, so tests
launch the **system-installed Google Chrome** (auto-updated by Google), not the bundled
Chromium. Install/select a channel with:

```bash
playwright install chrome          # Google Chrome (stable), system-wide
playwright install msedge          # Microsoft Edge
playwright install chrome-beta     # a newer Chrome build
```

Valid channels: `chrome`, `chrome-beta`, `chrome-dev`, `chrome-canary`, `msedge`,
`msedge-beta`, `msedge-dev`. To pin a specific Chrome version, install that channel's
browser and set the matching value in `config/execution.json` (e.g. `chrome-beta`).

> Because the default config uses `browser_channel: chrome`, make sure Google Chrome is
> available — either already installed, or via `playwright install chrome`. Leave
> `browser_channel` empty/null to use the bundled Chromium (version `149.0.7827.55` with
> the currently pinned Playwright) instead.

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

## 8. Run the tests

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
pytest --browser_name chrome -m full -n auto --tracing on --html=report.html
```

View a trace locally, or open [trace.playwright.dev](https://trace.playwright.dev/) and
drag-and-drop the `trace.zip` onto the page:

```bash
playwright show-trace "reports-results/test-results/<test-name>/trace.zip"
```

## Deactivate the virtual environment

When you are finished working:

```bash
deactivate
```
