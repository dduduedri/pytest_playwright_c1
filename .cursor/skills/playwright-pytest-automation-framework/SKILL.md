---
name: playwright-pytest-automation-framework
description: >
  Create, review, and extend a Python automation framework using Playwright,
  pytest, OOP page objects, reusable UI elements, API clients, Allure reporting,
  execution configuration, and external test data.
version: 1.1.0
---

# Playwright Pytest Automation Framework

## Purpose

Use this skill when creating, reviewing, refactoring, or extending a Python test
automation framework that contains:

- Playwright UI automation
- pytest test execution and fixtures
- API automation using Playwright `APIRequestContext`
- Object-oriented page objects
- Reusable UI element wrappers
- Allure steps and failure evidence
- External execution configuration
- External test data and user definitions
- UI, API, and end-to-end tests

The framework must remain simple enough for a new project while allowing future
growth without major restructuring.

---

# Required Project Structure

Use the following initial structure:

```text
playwright-pytest-framework/
├── ui/
│   ├── __init__.py
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── base_page.py
│   │   ├── login_page.py
│   │   └── dashboard_page.py
│   ├── elements/
│   │   ├── __init__.py
│   │   ├── base_element.py
│   │   ├── button.py
│   │   ├── text_box.py
│   │   ├── checkbox.py
│   │   └── dropdown.py
│   └── components/
│       ├── __init__.py
│       ├── header.py
│       └── navigation_menu.py
├── api/
│   ├── __init__.py
│   ├── base_api.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── auth_api.py
│   │   └── users_api.py
│   └── models/
│       ├── __init__.py
│       └── user.py
├── tests/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── test_login.py
│   │   └── test_dashboard.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── test_users_api.py
│   └── e2e/
│       ├── __init__.py
│       └── test_create_user_and_verify_ui.py
├── config/
│   ├── execution.json
│   └── environments.json
├── data/
│   ├── input_data/            # concrete values (credentials, request inputs)
│   │   └── credentials.json
│   ├── api_payloads/          # request-shape templates with <placeholders>
│   │   ├── login.json
│   │   └── create_order.json
│   └── expected_results/
│       └── order_confirmation.json
├── utils/
│   ├── __init__.py
│   ├── config_reader.py
│   ├── data_reader.py
│   └── logger.py
├── fixtures/
│   ├── __init__.py
│   ├── ui_fixtures.py
│   ├── api_fixtures.py
│   └── data_fixtures.py
├── conftest.py
├── pytest.ini
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

For a very small project, empty folders do not need to be created immediately.
Start with the folders that have active code and add the remaining folders when
they provide real value.

---

# Architecture Flow

## UI automation

```text
UI test
  ↓
Page object
  ↓
Reusable UI element
  ↓
Playwright Locator
```

## API automation

```text
API test
  ↓
Domain API client
  ↓
Base API
  ↓
Playwright APIRequestContext
```

## End-to-end automation

```text
E2E test
  ↓
API creates or prepares data
  ↓
UI verifies application behavior
  ↓
API performs cleanup when appropriate
```

---

# General Design Rules

1. Keep tests thin and readable.
2. Keep selectors inside page objects or reusable components.
3. Do not create a separate locator folder.
4. Do not duplicate Playwright locator methods.
5. Prefer composition over deep inheritance.
6. Use business-level page methods instead of exposing every click and fill.
7. Use reusable UI element classes only when they add reporting, validation, or
   framework behavior.
8. Use pytest fixtures for setup, dependency injection, and cleanup.
9. Keep execution configuration separate from test data.
10. Keep secrets outside committed JSON and YAML files.
11. Use Allure business steps at page/API level and nested technical steps at
    reusable element level.
12. Add new abstraction layers only when they solve repeated real problems.
13. Do not create empty `steps`, `flows`, `factories`, or `schemas` folders
    without a current use case.
14. Use type hints for public methods and fixtures.
15. Use explicit error messages when configuration or data is missing.

---

# UI Layer

## Pages

Place page objects under `ui/pages`.

A page object must:

- Receive a Playwright `Page`
- Define locators in its constructor
- Expose business actions
- Avoid assertions unless the method is explicitly a verification method
- Avoid direct test-data loading
- Avoid browser lifecycle management

Example:

```python
import allure
from playwright.sync_api import Page

from ui.elements.button import Button
from ui.elements.text_box import TextBox
from ui.pages.base_page import BasePage


class LoginPage(BasePage):
    PATH = "/login"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

        self.username = TextBox(
            page.get_by_label("Username"),
            "Username",
        )
        self.password = TextBox(
            page.get_by_label("Password"),
            "Password",
        )
        self.login_button = Button(
            page.get_by_role("button", name="Login"),
            "Login",
        )
        self.dashboard_title = page.get_by_role(
            "heading",
            name="Dashboard",
        )

    @allure.step("Open login page")
    def open_login_page(self) -> None:
        self.open(self.PATH)

    @allure.step("Login as user: {username}")
    def login(self, username: str, password: str) -> None:
        self.username.fill(username)
        self.password.fill(password, sensitive=True)
        self.login_button.click()
```

## Base Page

Keep `BasePage` small.

Allowed responsibilities include:

- Storing `Page`
- Storing the UI base URL
- Opening a relative application path
- Common page-level waiting that is genuinely shared

Do not wrap every Playwright method.

```python
from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    def open(self, path: str = "") -> None:
        url = f"{self.base_url}/{path.lstrip('/')}"
        self.page.goto(url)
```

## Locator Strategy

Use Playwright locators directly when constructing page elements.

Preferred order:

1. `get_by_role`
2. `get_by_label`
3. `get_by_placeholder`
4. `get_by_text`
5. `get_by_test_id`
6. CSS selector when necessary
7. XPath only as a last resort

Good:

```python
page.get_by_role("button", name="Save")
page.get_by_label("Email")
page.get_by_test_id("user-search")
```

Avoid helper methods that only repeat Playwright:

```python
def by_role(...):
    return page.get_by_role(...)
```

Do not create a separate `locators/` package. The locator, element name, and
page behavior should remain together.

---

# Reusable UI Elements

Place element wrappers under `ui/elements`.

Use wrappers when they add:

- Allure reporting
- Secret masking
- Standard validation
- Shared waiting behavior
- Consistent error messages
- Framework-specific behavior

Do not create wrappers only to rename Playwright methods.

## Base Element

```python
from playwright.sync_api import Locator


class BaseElement:
    def __init__(self, locator: Locator, name: str) -> None:
        self.locator = locator
        self.name = name

    def is_visible(self) -> bool:
        return self.locator.is_visible()

    def wait_until_visible(self) -> None:
        self.locator.wait_for(state="visible")
```

## Button

```python
import allure

from ui.elements.base_element import BaseElement


class Button(BaseElement):
    def click(self) -> None:
        with allure.step(f"Click button: {self.name}"):
            self.locator.click()

    def is_enabled(self) -> bool:
        with allure.step(f"Check button is enabled: {self.name}"):
            return self.locator.is_enabled()
```

## Text Box

```python
import allure

from ui.elements.base_element import BaseElement


class TextBox(BaseElement):
    def fill(self, value: str, *, sensitive: bool = False) -> None:
        displayed_value = "***" if sensitive else value

        with allure.step(
            f"Fill text box '{self.name}' with '{displayed_value}'"
        ):
            self.locator.fill(value)

    def clear(self) -> None:
        with allure.step(f"Clear text box: {self.name}"):
            self.locator.clear()

    def get_value(self) -> str:
        with allure.step(f"Get value from text box: {self.name}"):
            return self.locator.input_value()
```

Never expose passwords, access tokens, API keys, or other secrets in Allure
step names or attachments.

---

# Components

Place reusable sections used across multiple pages under `ui/components`.

Examples:

- Header
- Navigation menu
- Dialog
- Data table
- Toast notification
- Date picker

Use composition:

```python
class DashboardPage(BasePage):
    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.header = Header(page)
        self.navigation = NavigationMenu(page)
```

Do not create deep inheritance chains such as:

```text
BasePage
  └── AuthenticatedPage
      └── AdminPage
          └── UserManagementPage
```

---

# API Layer

## Base API

Place shared request execution in `api/base_api.py`.

Responsibilities:

- Execute HTTP methods
- Apply common headers
- Handle expected status codes
- Provide useful failure messages
- Return Playwright `APIResponse`

```python
from collections.abc import Collection
from typing import Any

import allure
from playwright.sync_api import APIRequestContext, APIResponse


class ApiRequestError(RuntimeError):
    pass


class BaseApi:
    def __init__(self, request_context: APIRequestContext) -> None:
        self.request_context = request_context

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_status: int | Collection[int] = 200,
    ) -> APIResponse:
        with allure.step(f"{method.upper()} {endpoint}"):
            response = self.request_context.fetch(
                endpoint,
                method=method,
                data=data,
                params=params,
                headers=headers,
                fail_on_status_code=False,
            )

            valid_statuses = (
                {expected_status}
                if isinstance(expected_status, int)
                else set(expected_status)
            )

            if response.status not in valid_statuses:
                raise ApiRequestError(
                    f"{method.upper()} {endpoint} failed. "
                    f"Expected {sorted(valid_statuses)}, "
                    f"received {response.status}. "
                    f"Response: {response.text()}"
                )

            return response
```

## API Clients

Place domain-specific clients under `api/clients`.

Organize by business resource, not by HTTP method.

Good:

```text
auth_api.py
users_api.py
orders_api.py
```

Avoid:

```text
get_requests.py
post_requests.py
delete_requests.py
```

Example:

```python
import allure
from playwright.sync_api import APIRequestContext, APIResponse

from api.base_api import BaseApi


class UsersApi(BaseApi):
    def __init__(self, request_context: APIRequestContext) -> None:
        super().__init__(request_context)

    @allure.step("Get user: {user_id}")
    def get_user(self, user_id: int) -> APIResponse:
        return self.request(
            "GET",
            f"/users/{user_id}",
            expected_status=200,
        )

    @allure.step("Create user: {email}")
    def create_user(self, name: str, email: str) -> APIResponse:
        return self.request(
            "POST",
            "/users",
            data={
                "name": name,
                "email": email,
            },
            expected_status={200, 201},
        )
```

## API Models

Add `api/models` when request or response dictionaries become repeated or
complex.

Use dataclasses for simple typed models:

```python
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CreateUserRequest:
    name: str
    email: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
        }
```

Do not introduce models for one-line payloads unless typing or reuse justifies
them. For data-driven bodies, prefer a JSON template under `api_payloads/` with
`<placeholders>` (see **Payload Templating**) over a dataclass whose only job is to
turn a dict into the same dict.

---

# Tests

## UI Tests

Place UI tests under `tests/ui`.

UI tests should:

- Use page objects
- Use pytest fixtures
- Use Playwright `expect`
- Avoid raw selectors
- Avoid direct configuration-file reading
- Avoid direct credential-file reading
- Avoid browser setup inside the test

```python
import pytest
from playwright.sync_api import expect

from ui.pages.login_page import LoginPage
from utils.credentials import UserCredentials


@pytest.mark.ui
@pytest.mark.smoke
def test_successful_login(
    login_page: LoginPage,
    admin_user: UserCredentials,
) -> None:
    login_page.open_login_page()
    login_page.login(
        username=admin_user.username,
        password=admin_user.password,
    )

    expect(login_page.dashboard_title).to_be_visible()
```

## API Tests

Place API tests under `tests/api`.

```python
import pytest

from api.clients.users_api import UsersApi


@pytest.mark.api
def test_get_user(users_api: UsersApi) -> None:
    response = users_api.get_user(1)

    assert response.status == 200
    assert response.json()["id"] == 1
```

## E2E Tests

Place tests combining API and UI under `tests/e2e`.

Use the API for fast setup and cleanup. Use the UI only for behavior that must
be verified through the browser.

---

# Configuration

Place framework execution settings under `config`.

Recommended `config/execution.json`:

```json
{
  "application_url": "http://rahulshettyacademy.com/client",
  "api_url": "https://api.example.com",
  "browser": "chromium",
  "browser_channel": "chrome",
  "headless": false,
  "default_timeout_ms": 30000
}
```

Use:

- `browser: chromium` for the Playwright browser type
- `browser_channel: chrome` when branded Google Chrome is required

### Headed / Headless

When the browser is launched from the framework's own `browser_setup` fixture (not the
`pytest-playwright` `page` fixture), the built-in `--headed` flag does not reach it.
Drive headed/headless from `config/execution.json` (`"headless"`) as the default, and
allow a per-run CLI override so it is still convenient to switch:

```python
# conftest.py: --headed comes from pytest-playwright; add a --headless counterpart
parser.addoption("--headless", action="store_true", default=False)

# browser_setup: CLI flag wins over the config default
headless = execution_config.headless
if request.config.getoption("--headed", default=False):
    headless = False
elif request.config.getoption("--headless", default=False):
    headless = True
```

Use `getoption(..., default=False)` so the lookup is safe even if a flag is not
registered.

Do not use `.properties` unless integration with an existing Java-oriented
system requires it. JSON is suitable for a Python project and supports future
nested configuration.

## Configuration Reader

```python
import json
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXECUTION_FILE = PROJECT_ROOT / "config" / "execution.json"


@dataclass(frozen=True)
class ExecutionConfig:
    application_url: str
    api_url: str
    browser: str
    browser_channel: str | None
    headless: bool
    default_timeout_ms: int

    @classmethod
    def load(cls) -> "ExecutionConfig":
        if not EXECUTION_FILE.exists():
            raise FileNotFoundError(
                f"Execution configuration was not found: {EXECUTION_FILE}"
            )

        with EXECUTION_FILE.open(encoding="utf-8") as file:
            data = json.load(file)

        return cls(
            application_url=data["application_url"],
            api_url=data["api_url"],
            browser=data.get("browser", "chromium"),
            browser_channel=data.get("browser_channel"),
            headless=data.get("headless", True),
            default_timeout_ms=data.get("default_timeout_ms", 30000),
        )
```

---

# Test Data

Place test data under `data`, split by role:

```text
data/
├── input_data/                 # concrete VALUES a test feeds in
│   └── credentials.json        # per-user login records (git-ignored)
├── api_payloads/               # request-body SHAPES (templates with <placeholders>)
│   ├── login.json
│   └── create_order.json
└── expected_results/           # expected values assertions compare against
    └── order_confirmation.json
```

Keep the two data roles separate:

- `data/input_data/` holds concrete values a test supplies at run time (e.g. credentials).
- `data/api_payloads/` holds the request-body *shape* as a template. Values are not
  hard-coded there; they are injected via placeholders — either passed directly at the
  call site or sourced from `input_data`.

`credentials.json` maps a named key to each user record and must not contain real
production passwords; keep the file out of version control:

```json
{
  "user_a": { "userEmail": "a@example.com", "UserPassword": "..." },
  "user_b": { "userEmail": "b@example.com", "UserPassword": "..." }
}
```

For truly sensitive values, prefer `.env`, CI credentials, or a secret manager and
commit `.env.example`, not `.env`.

## Payload Templating

Payload files under `api_payloads/` may contain `<placeholder>` tokens that are
substituted at load time. This keeps the request *shape* in one file while the *values*
are supplied at the call site, so the same template serves many cases.

`data/api_payloads/create_order.json` (shape only):

```json
{
  "orders": [
    { "country": "<country>", "productOrderedId": "<productOrderedId>" }
  ]
}
```

Substitution happens in `load_api_payload(name, **params)` — pass the values directly:

```python
payload = load_api_payload(
    "create_order",
    country="India",
    productOrderedId="6960eac0c941646b7a8b3e68",
)
# -> {"orders": [{"country": "India", "productOrderedId": "6960eac0c941646b7a8b3e68"}]}
```

Values may be literals at the call site (above) or sourced from a data file when they
need to vary per run (e.g. read them from `input_data/` and pass with `**values`).

Rules for the substitution engine:

- An **exact** token (`"<order_id>"`) is replaced with the raw value, preserving its
  type (int stays int, nested object stays object).
- An **embedded** token (`"id-<order_id>-x"`) is replaced with `str(value)`.
- A token with no matching argument raises a clear error naming the file, so a stray
  `<placeholder>` never reaches the API.

Because login credentials in this project are not treated as production secrets, the
login body is also a template (`api_payloads/login.json` with `<userEmail>` /
`<userPassword>`) fed from `input_data/credentials.json`. If credentials were real
secrets, keep them out of committed files and inject from the environment instead.

## Data Reader

```python
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DATA_DIR = DATA_DIR / "input_data"
_PLACEHOLDER = re.compile(r"<([^<>]+)>")


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Data file was not found: {path}")
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _render(value: Any, params: dict, source: str) -> Any:
    if isinstance(value, dict):
        return {k: _render(v, params, source) for k, v in value.items()}
    if isinstance(value, list):
        return [_render(v, params, source) for v in value]
    if isinstance(value, str):
        exact = _PLACEHOLDER.fullmatch(value)
        if exact:                                   # keep native type
            return _lookup(exact.group(1), params, source)
        return _PLACEHOLDER.sub(lambda m: str(_lookup(m.group(1), params, source)), value)
    return value


def _lookup(token: str, params: dict, source: str) -> Any:
    if token not in params:
        raise KeyError(f"Payload '{source}' needs placeholder <{token}>; not provided.")
    return params[token]


def load_api_payload(name: str, **params: Any) -> dict:
    """Request-body TEMPLATE from data/api_payloads/<name>.json with <placeholders>
    replaced by the given keyword arguments."""
    payload = _read_json(DATA_DIR / "api_payloads" / f"{name}.json")
    return _render(payload, params, name)
```

## Stable Parametrize IDs

When parametrizing over records (dicts), pytest falls back to positional ids like
`user_credential0`. Provide readable ids so console output, the `[...]` node id, and
per-test artifact folders are meaningful. If the data file maps named keys to records,
expose the keys as ids:

```python
def load_credentials() -> list[dict]:
    return list(_read_json(INPUT_DATA_DIR / "credentials.json").values())

def load_credential_ids() -> list[str]:
    return list(_read_json(INPUT_DATA_DIR / "credentials.json").keys())


@pytest.mark.parametrize("user", load_credentials(), ids=load_credential_ids())
def test_login(user): ...
```

`ids=` accepts a list (matched to values by position) or a callable that receives each
value. Keep the credentials file out of version control (it holds secrets).

---

# Fixtures

For a small project, fixtures may initially remain in `conftest.py`.

When `conftest.py` grows, move them into:

```text
fixtures/
├── ui_fixtures.py
├── api_fixtures.py
└── data_fixtures.py
```

Keep root `conftest.py` small:

```python
pytest_plugins = (
    "fixtures.ui_fixtures",
    "fixtures.api_fixtures",
    "fixtures.data_fixtures",
)
```

## UI Fixture

```python
import pytest
from playwright.sync_api import Page

from ui.pages.login_page import LoginPage
from utils.config_reader import ExecutionConfig


@pytest.fixture
def login_page(
    page: Page,
    execution_config: ExecutionConfig,
) -> LoginPage:
    page.set_default_timeout(
        execution_config.default_timeout_ms
    )

    return LoginPage(
        page=page,
        base_url=execution_config.application_url,
    )
```

## API Fixture

```python
from collections.abc import Iterator

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from api.clients.users_api import UsersApi
from utils.config_reader import ExecutionConfig


@pytest.fixture
def api_context(
    playwright: Playwright,
    execution_config: ExecutionConfig,
) -> Iterator[APIRequestContext]:
    context = playwright.request.new_context(
        base_url=execution_config.api_url,
        extra_http_headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )

    yield context

    context.dispose()


@pytest.fixture
def users_api(api_context: APIRequestContext) -> UsersApi:
    return UsersApi(api_context)
```

Use `yield` fixtures for resources that require cleanup.

---

# Allure Reporting

Use two reporting levels.

## Business-Level Steps

Place business-level steps on:

- Page methods
- API client methods
- Cross-page workflows

Example:

```python
@allure.step("Login as user: {username}")
def login(self, username: str, password: str) -> None:
    ...
```

## Technical Nested Steps

Place technical nested steps on reusable UI elements:

```python
with allure.step(f"Click button: {self.name}"):
    self.locator.click()
```

Expected report:

```text
Login as user: admin@example.com
├── Fill text box 'Username' with 'admin@example.com'
├── Fill text box 'Password' with '***'
└── Click button: Login
```

## Failure Evidence

Attach screenshots on failure rather than after every action.

```python
import allure
import pytest
from playwright.sync_api import Page


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo,
):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    page: Page | None = item.funcargs.get("page")

    if page is None or page.is_closed():
        return

    allure.attach(
        page.screenshot(full_page=True),
        name="Failure screenshot",
        attachment_type=allure.attachment_type.PNG,
    )
```

Recommended pytest-playwright options:

```ini
[pytest]
addopts =
    --tracing=retain-on-failure
    --screenshot=only-on-failure
```

## Rich Failure Artifacts

On failure, attach diagnostic evidence in one place (a function-scoped context/page
fixture teardown), gated so passing tests stay clean. Useful attachments:

- Full-page screenshot of the failure state.
- A readable traceback (optionally filtered to project frames only).
- Browser console errors/warnings and uncaught page exceptions.
- Network failures and HTTP error responses (4xx/5xx).
- Video recording of the run (when enabled).

Collect console/network problems with Playwright event listeners registered before
navigation, then attach them during teardown:

```python
console_errors: list[str] = []
network_errors: list[str] = []

page.on("console", lambda m: console_errors.append(f"[{m.type}] {m.text}")
        if m.type in ("error", "warning") else None)
page.on("pageerror", lambda e: console_errors.append(f"[pageerror] {e}"))
page.on("requestfailed", lambda r: network_errors.append(
    f"[requestfailed] {r.method} {r.url} :: {r.failure}"))
page.on("response", lambda r: network_errors.append(
    f"[HTTP {r.status}] {r.request.method} {r.url}") if r.status >= 400 else None)
```

These listeners are on the browser `page`, so they capture UI-driven traffic only.
API-layer calls go through a separate `APIRequestContext`; log non-2xx responses in
the API client if you need that evidence too.

## Keep Set up / Tear down Clean

pytest logs every fixture finalizer. Allure renders higher-scope and yield-finalizer
wrappers (e.g. `context_setup::<lambda>`) as status-less **"Unknown"** rows, which add
noise. Remove them with a `pytest_sessionfinish` hook that strips status-less
`befores`/`afters` from the Allure `*-container.json` files, keeping only meaningful
steps (such as the teardown that carries the failure attachments).

## Clean Result Folders Together

If custom outputs (traces, videos) are written under a results root, extend
`--clean-alluredir` with a `pytest_configure` hook so one flag clears all of them and
runs don't accumulate stale artifacts. Guard against xdist workers so only the
controller cleans, before workers start writing.

---

# pytest Configuration

Recommended `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*

markers =
    ui: UI automation tests
    api: API automation tests
    e2e: Combined UI and API tests
    smoke: Critical smoke tests
    regression: Full regression tests

addopts =
    -ra
    --tracing=retain-on-failure
    --screenshot=only-on-failure
```

---

# Dependencies

Recommended initial `requirements.txt`:

```text
pytest
playwright
pytest-playwright
python-dotenv
allure-pytest
pytest-xdist
```

Installation:

```bash
pip install -r requirements.txt
playwright install
playwright install ffmpeg   # only needed when recording video (--video on)
```

`allure-pytest` provides the `--alluredir`/`--clean-alluredir` options; if pytest reports
them as *unrecognized arguments*, the plugin is not installed in the interpreter running
pytest. Run via the project's venv (e.g. `python -m pytest`) and confirm the plugin loads
with `pytest --version`. Video recording additionally needs the ffmpeg binary above,
otherwise Playwright raises "Video rendering requires ffmpeg binary".

Common commands:

```bash
pytest
pytest -m ui
pytest -m api
pytest -m smoke
pytest --headed
pytest -n 4
pytest --alluredir=allure-results
allure serve allure-results
```

---

# Naming Conventions

Use `snake_case` for:

- Python files
- Functions
- Methods
- Fixtures
- Variables

Use `PascalCase` for:

- Classes
- Dataclasses
- Exceptions

Examples:

```text
login_page.py
users_api.py
test_create_user.py
```

```python
class LoginPage:
    pass


def test_successful_login():
    pass
```

Test names must describe behavior:

Good:

```python
def test_admin_can_login_with_valid_credentials():
    ...
```

Avoid:

```python
def test_login_1():
    ...
```

---

# When to Add More Layers

## Add `flows/` when:

- A business operation uses multiple pages
- A workflow combines UI and API
- The same multi-page sequence is repeated
- A page class is becoming responsible for another page

## Add `factories/` when:

- Test objects require unique generated data
- Payload generation is repeated
- Tests contain repeated object-building logic

## Add `schemas/` when:

- JSON schema validation is required
- API contracts are stored and validated

## Add `assertions/` when:

- The same domain validations are repeated
- Custom assertion messages are needed
- Assertions require multi-field comparison

Do not add these folders only for architectural appearance.

---

# Patterns to Avoid

Do not generate:

## Separate Locator Classes

```python
class LoginLocators:
    USERNAME = "#username"
```

Keep locators in the page or component where they are used.

## Duplicate Step Classes

```python
class LoginSteps:
    def login(self, username, password):
        self.login_page.login(username, password)
```

A step or flow class must add orchestration, not only delegate one method.

## Giant Base Page

Do not create a base page that wraps every Playwright action.

## Raw Selectors in Tests

Avoid:

```python
page.locator("#username").fill("admin")
```

Use the page object.

## Secrets in Data Files

Avoid:

```json
{
  "password": "RealPassword123"
}
```

## Sleep-Based Waiting

Avoid:

```python
time.sleep(5)
```

Use Playwright auto-waiting, locator expectations, or explicit state-based
waiting.

## Broad Utility Dumping Ground

Do not place unrelated helpers into a large `utils.py`.

Create focused modules such as:

```text
config_reader.py
data_reader.py
logger.py
```

---

# Code Generation Checklist

When generating or reviewing framework code, verify:

- [ ] UI and API code are separated.
- [ ] Tests are separated into UI, API, and E2E.
- [ ] Locators are not stored in a separate locator package.
- [ ] Reusable element wrappers add real value.
- [ ] Page methods describe business actions.
- [ ] API clients are organized by domain resource.
- [ ] Fixtures handle setup and cleanup.
- [ ] Execution configuration is under `config`.
- [ ] Test data is under `data`, split into `input_data` (values) and `api_payloads`
      (shape templates with `<placeholders>`).
- [ ] Payload templates carry no hard-coded values; runtime values are injected.
- [ ] Passwords and tokens are external secrets.
- [ ] Sensitive values are masked in Allure.
- [ ] Screenshots and traces are retained on failure.
- [ ] No fixed sleeps are used.
- [ ] Type hints are present.
- [ ] Error messages explain missing configuration or data.
- [ ] New abstraction layers are justified by reuse.

---

# Expected Assistant Behavior

When this skill is active:

1. Preserve this architecture unless the user explicitly requests another design.
2. Generate complete, copy-ready files when asked.
3. Show exact target paths above code examples.
4. Keep beginner implementations simple.
5. Explain when a proposed abstraction is unnecessary.
6. Prefer Playwright-native behavior over custom wrappers.
7. Never put secrets in committed files.
8. Use synchronous Playwright APIs unless async is explicitly required.
9. Use pytest fixtures instead of manual test-class setup.
10. Use Allure steps without exposing sensitive values.
11. Recommend incremental growth rather than creating an enterprise-sized
    framework before it is needed.
12. When modifying existing code, preserve the current naming and architecture
    unless a change is necessary and clearly explained.
