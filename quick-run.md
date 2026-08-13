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

> **Execution defaults live in** `config/execution.json`**.** It sets `application_url`,
> `api_url`, `browser`, `browser_channel`, `default_timeout_ms`, and the default
> `"headless"` value (`true` = headless, `false` = headed).
>
> **Headed/headless can also be overridden per run from the command line** (the flag wins
> over the config default):
>
> ```powershell
> pytest --browser_name chrome -m full --headed     # force headed this run
> pytest --browser_name chrome -m full --headless   # force headless this run
> pytest --browser_name chrome -m full              # use config/execution.json default
> ```

```powershell
# 6) Run the full suite (Chrome, parallel, tracing + video, clean old Allure results)
#    Add --headed to watch the browser, or --headless to force headless.
pytest --browser_name chrome -m full -n auto --headless --tracing on --video on --clean-alluredir

# 7) Open the Allure report
allure serve reports-results/allure-results

# 8) Open a saved Playwright trace
playwright show-trace "reports-results/test-results/test_create_order_and_verify_ui[user_a]/trace.zip"
```

> Already set up? Just activate the venv (`.\.venv\Scripts\Activate.ps1`) and jump to step 6.

