# Running This Project in Cursor

A complete guide to set up and run this **pytest + Playwright** project inside the Cursor IDE.

## 1. Prerequisites

- **Python 3.9+** installed — check with `py --version` (Windows) or `python3 --version` (macOS/Linux)
- **Git** installed (`git --version`)
- The project opened as a folder in Cursor (**File → Open Folder** → `pytest_playwright`)

## 2. Install the Python extension

1. Open Extensions: `Ctrl + Shift + X`
2. Search for **Python** (publisher: `ms-python.python`, by Microsoft) and install it.
   - This automatically includes the **Python Debugger** and **Test Explorer** integration.

## 3. Create and activate the virtual environment

Open the integrated terminal (`` Ctrl + ` ``) and run:

```powershell
py -m venv .venv                      # create the virtual environment
.\.venv\Scripts\python.exe --version  # verify the venv interpreter
.\.venv\Scripts\Activate.ps1          # activate it
```

> If PowerShell blocks activation, run once:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

For full cross-platform setup, see [INSTALL.md](INSTALL.md).

## 4. Install dependencies and browsers

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install
```

`playwright install` downloads the Chromium/Firefox/WebKit binaries the tests drive.

## 5. Select the Python interpreter

1. Command Palette: `Ctrl + Shift + P`
2. Run **Python: Select Interpreter**
3. Choose the project virtual environment: `.venv\Scripts\python.exe`

## 6. Test configuration (already set up)

This repo ships a `.vscode/settings.json` that enables pytest discovery:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["."]
}
```

If tests don't appear, run **Developer: Reload Window**, then `Ctrl + Shift + P` → **Python: Configure Tests** → **pytest** → root directory.

## 7. Run the tests

### Inline gutter buttons

After discovery, a green ▶ **Run Test** icon appears in the gutter next to each test
function/class. Click it to run, or right-click for **Debug Test**.

### Testing panel

Click the flask/beaker icon in the left sidebar to open the **Testing** panel, where you
can run/debug all tests and inspect pass/fail results.

### Terminal

```powershell
# run everything
pytest -s

# run a single file, headed (visible browser)
pytest -s tests/e2e/test_api_login_then_ui_login.py --headed

# choose the browser (see custom option below)
pytest -s tests/e2e/test_api_login_then_ui_login.py --headed --browser_name firefox

# run one test by name
pytest -s tests/ui/test_login.py --headed

# run in parallel across CPU cores (pytest-xdist)
pytest -n auto

# run with a specific number of parallel workers
pytest -n 3

# generate a self-contained HTML report (pytest-html)
pytest --html=report.html --self-contained-html

# record a Playwright trace per test -> reports-results/test-results/<test-name>/trace.zip
pytest --tracing on

# combined: browser, marker, parallel, tracing, HTML report
pytest --browser_name chromium -m e2e -n auto --tracing on --html=report.html

# view a trace locally (or drag-and-drop the zip onto https://trace.playwright.dev/)
playwright show-trace "reports-results/test-results/<test-name>/trace.zip"
```

## 8. Project-specific options

This project defines **custom command-line options** in `conftest.py`:

| Option | Values | Default | Purpose |
|--------|--------|---------|---------|
| `--env` | any key of `config/environment.json` | `"environment"` in `config/execution.json` | Environment to run against: it supplies the app URL, the API host and the other service URLs |
| `--browser_name` | `chromium`, `firefox`, `webkit` | `browser` in `config/execution.json` | Selects which browser the `browser_setup` fixture launches |
| `--url` | any URL | the chosen environment's `ui` | Overrides only the application URL passed to UI fixtures |

- Tests launch in **headed** mode by default (`"headless": false` in `config/execution.json`). Override per run with `--headed` or `--headless` — the CLI flag wins over the config default.
- The gutter/Testing-panel runners use `pytestArgs` (`["."]`), so they run with the default
  `--browser_name chromium`. To make GUI runs target a specific browser, add it to `pytestArgs`
  in `.vscode/settings.json`, e.g. `["--browser_name", "firefox", "."]`.

## 9. Debugging

- Set breakpoints by clicking left of a line number.
- Use the gutter **Debug Test** action, or the **Testing** panel's debug icon.
- The Python Debugger stops at breakpoints so you can inspect variables and step through code.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No run buttons in gutter | Ensure Python extension is installed, interpreter is the `.venv`, then **Reload Window** |
| `ModuleNotFoundError: playwright` | Activate the venv and run `pip install -r requirements.txt` |
| Browser fails to launch | Run `playwright install` to download browser binaries |
| Tests not discovered | Run **Python: Configure Tests** → pytest → root directory |
| PowerShell won't activate venv | Run the `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` command above |
