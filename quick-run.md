# Quick Run

From-scratch setup and execution, assuming a fresh clone with **no** `.venv` **yet**.
Commands are for **Windows PowerShell** (this project's default shell).

## 1) One-time setup (from scratch after clone)

```powershell
# 0) Check Python is available (use the Windows launcher)
py --version

# 1) Create the virtual environment
py -m venv .venv

# 2) Activate it (prompt should now show "(.venv)")
.\.venv\Scripts\Activate.ps1
# If activation is blocked by execution policy, run PowerShell once as:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3) Upgrade pip and install Python dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4) Install the Playwright browsers + the ffmpeg binary (needed for --video on)
python -m playwright install
python -m playwright install ffmpeg

# 5) Verify pytest sees all plugins (expect: allure-pytest, playwright, xdist, html, ...)
python -m pytest --version
```

> Command 6 below (`allure serve`) needs the **Allure CLI**, which is separate from the
> `allure-pytest` Python package. If `allure` is not installed, see
> [INSTALL.md → Install the Allure CLI](_documentation/INSTALL.md#6-install-the-allure-cli-optional-for-viewing-reports).



## 2) Run and view

> **Defaults live in two files under** `config/`**.** `environment.json` names the
> application under test (one entry per environment, each with `ui` and `apiHost`);
> `execution.json` sets `browser`, `browser_channel`, `default_timeout_ms`, the default
> `"headless"` value (`true` = headless, `false` = headed; it ships as `false`, so runs are
> headed unless you pass `--headless`) and the default `environment`.
>
> **The environment is chosen per run with** `--env` (a key of `environment.json`);
> without it the `environment` value in `execution.json` is used:
>
> ```powershell
> pytest -m ui --env c1-env-auto-testing-auth-1445
> pytest -m ui --env c1-env-automation-testing-1444
> ```
>
> **Headed/headless can also be overridden per run from the command line** (the flag wins
> over the config default):
>
> ```powershell
> pytest --browser_name chromium -m e2e --headed     # force headed this run
> pytest --browser_name chromium -m e2e --headless   # force headless this run
> pytest --browser_name chromium -m e2e              # use config/execution.json default (headed)
> ```

```powershell
# 6) Run the example e2e tests (Chromium, parallel, tracing + video, clean old Allure results)
#    Add --headed to watch the browser, or --headless to force headless.
pytest --browser_name chromium -m e2e -n auto --headed --tracing on --video on --clean-alluredir

# 7) Open the Allure report
allure serve reports-results/allure-results

# 8) Open a saved Playwright trace
playwright show-trace "reports-results/test-results/test_api_login_then_ui_login[user_a]/trace.zip"
```

> Already set up? Just activate the venv (`.\.venv\Scripts\Activate.ps1`) and jump to step 6.

> **On a fresh clone steps 6-8 report only skipped tests and produce no trace.** The three
> example tests carry `@pytest.mark.skip` until they point at a real application — see
> [README.md](README.md#point-the-template-at-your-application). Remove the marker from a
> test once its page object / API client is yours, and the artifacts above appear.

