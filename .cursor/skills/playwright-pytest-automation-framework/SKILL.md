---
name: playwright-pytest-automation-framework
description: >
  Create, review, and extend a Python automation framework using Playwright,
  pytest, OOP page objects, reusable UI elements, API clients, Allure reporting,
  execution configuration, and external test data.
version: 2.0.0
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

For porting tests out of the legacy Java/TestNG framework, use the
`migrate-java-tests-to-pytest` skill together with this one: it adds the
translation tables, the per-test ledger, and the migration percentage report,
while the rules below still decide what the resulting code must look like.

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
│   │   └── login_page.py
│   ├── elements/
│   │   ├── __init__.py
│   │   ├── base_element.py
│   │   ├── button.py
│   │   ├── text_box.py
│   │   ├── checkbox.py
│   │   └── dropdown.py
│   └── components/
│       └── __init__.py
├── api/
│   ├── __init__.py
│   ├── base_api.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── auth_api.py
│   │   └── users_api.py
│   └── models/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   └── test_login.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── test_auth_api.py
│   └── e2e/
│       ├── __init__.py
│       └── test_api_login_then_ui_login.py
├── config/
│   ├── environment.json       # one entry per environment (the target app's URLs)
│   └── execution.json         # environment choice, browser, headless, timeouts
├── data/
│   ├── input_data/            # concrete values (credentials, request inputs)
│   │   └── credentials.json   # git-ignored; created per machine
│   ├── api_payloads/          # request-shape templates with <placeholders>
│   │   ├── login.json
│   │   └── create_user.json
│   └── expected_results/
│       └── login.json
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
16. This repository is a **template**: the example `LoginPage`, `AuthApi`, and the three
    example tests are references to replace. Example tests carry `@pytest.mark.skip`
    until they point at a real application. Do not commit product-specific values into
    `config/` or `data/`.

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

Example (EXAMPLE page object — replace locators for your application):

```python
import allure
from playwright.sync_api import expect

from ui.elements.button import Button
from ui.elements.text_box import TextBox
from ui.pages.base_page import BasePage
from utils.data_reader import load_expected_result


class LoginPage(BasePage):

    def __init__(self, page):
        super().__init__(page)
        self.email = TextBox(page.get_by_label("Email"), "Email")
        self.password = TextBox(page.get_by_label("Password"), "Password")
        self.login_button = Button(page.get_by_role("button", name="Login"), "Login")

    def login(self, email, password):
        self.email.fill(email)
        self.password.fill(password, mask=True)
        self.login_button.click()

    def login_and_continue(self, email, password) -> None:
        with allure.step(f"UI · login (user: {email})"):
            self.login(email, password)

    @allure.step("UI · verify the user is logged in")
    def verify_logged_in(self) -> None:
        expected_heading = load_expected_result("login")["logged_in_heading"]
        with allure.step(f"Assert heading is visible · expected='{expected_heading}'"):
            expect(self.page.get_by_role("heading", name=expected_heading)).to_be_visible()
```

Navigation to the application URL is handled by the `context_setup` fixture (via
`--url` / `config/environment.json`), not by the page object.

## Base Page

Keep `BasePage` small.

Allowed responsibilities include:

- Storing `Page`
- Navigating to an absolute URL when a page genuinely needs it
- Common page-level waiting that is genuinely shared

Do not wrap every Playwright method.

```python
from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def goto(self, url: str):
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
    def fill(self, value: str, mask: bool = False) -> None:
        shown = "***" if mask else value

        with allure.step(f"Fill '{self.name}' = '{shown}'"):
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
    def __init__(self, page):
        super().__init__(page)
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

- Execute HTTP methods, one wrapper per verb
- Apply common headers
- Record each call as an Allure step
- Attach response metadata, and the body when the call failed
- Mask secret-looking fields in every attached payload
- Return Playwright `APIResponse`, so clients decide what a failure means

Status checking stays in the domain client (an assertion with a domain message), not in
`BaseApi`; that keeps the base free of per-endpoint expectations.

```python
class BaseApi:
    def __init__(self, request_context: APIRequestContext):
        self.request_context = request_context

    def _default_headers(self, headers):
        merged = {"Content-Type": "application/json"}
        if headers:
            merged.update(headers)
        return merged

    def _attach_response(self, response: APIResponse) -> None:
        attach_text("response · meta", f"status: {response.status}\nurl: {response.url}")
        if response.status < 400:
            return
        attach_text("response · error body", response.text()[:2000])

    def post(self, endpoint, data=None, headers=None):
        with allure.step(f"POST {endpoint}"):
            response = self.request_context.post(
                endpoint, data=data, headers=self._default_headers(headers)
            )
            self._attach_response(response)
            log.info("POST %s -> %s", endpoint, response.status)
            return response
```

`get`, `put` and `delete` follow the same shape. `attach_json` runs every payload through
`mask_secrets`, so any key containing `password`, `token`, `authorization`, `secret` or
`apikey` is redacted before it reaches the report.

## API Clients

Place domain-specific clients under `api/clients`.

Organize by business resource, not by HTTP method.

Good:

```text
auth_api.py
users_api.py
```

Avoid:

```text
get_requests.py
post_requests.py
delete_requests.py
```

Example (EXAMPLE API client — replace the endpoint and response field for your API):

```python
import allure

from api.base_api import BaseApi, attach_json, attach_text
from utils.data_reader import load_api_payload

LOGIN_ENDPOINT = "/api/auth/login"


class AuthApi(BaseApi):

    def login(self, email, password) -> str:
        with allure.step(f"API · get auth token (user: {email})"):
            payload = load_api_payload("login", email=email, password=password)
            attach_json("request · login payload", payload)

            response = self.post(LOGIN_ENDPOINT, data=payload)

            assert response.ok, (
                f"Login failed for {email} (status {response.status}): {response.text()}"
            )
            token = response.json()["token"]
            attach_text("output · auth token (truncated)", f"{token[:12]}…")
            return token
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
import allure
import pytest

from ui.pages.login_page import LoginPage
from utils.data_reader import load_credential_ids, load_credential_users


@pytest.mark.ui
@pytest.mark.skip(reason="Template example - update LoginPage for your app, then remove this marker")
@pytest.mark.parametrize("user", load_credential_users(), ids=load_credential_ids())
def test_login(context_setup, user, user_passwords):
    user_password = user_passwords[user]

    login_page = LoginPage(context_setup)
    login_page.login_and_continue(user, user_password)
    login_page.verify_logged_in()
```

## API Tests

Place API tests under `tests/api`.

```python
import allure
import pytest

from api.clients.auth_api import AuthApi
from utils.data_reader import load_credential_ids, load_credential_users


@pytest.mark.api
@pytest.mark.skip(reason="Template example - update AuthApi for your app, then remove this marker")
@pytest.mark.parametrize("user", load_credential_users(), ids=load_credential_ids())
def test_login_returns_token(auth_api: AuthApi, user, user_passwords):
    token = auth_api.login(user, user_passwords[user])

    assert token, "expected an auth token in the login response"
```

## E2E Tests

Place tests combining API and UI under `tests/e2e`.

Use the API for fast setup and cleanup. Use the UI only for behavior that must
be verified through the browser.

---

# Configuration

Place framework settings under `config`, split by the question they answer.

`config/environment.json` — WHERE the run points: one entry per environment, keyed by
environment name, so several environments live side by side. `ui` and `apiHost` are
required; add only the extra service URLs the suite actually calls.

```json
{
  "my-env": {
    "ui": "https://example.com",
    "apiHost": "https://api.example.com",
    "keycloakUrl": "https://keycloak.example.com/auth/realms/my-env"
  }
}
```

`config/execution.json` — HOW the run behaves, plus the default environment
(`environment` is needed only when environment.json defines more than one):

```json
{
  "environment": "my-env",
  "browser": "chromium",
  "browser_channel": null,
  "headless": false,
  "default_timeout_ms": 30000,
  "test_id_attribute": "data-testid",
  "ignore_https_errors": false
}
```

Keeping the target application in its own file means switching environment never touches
run settings: adding an environment is a new entry, and running against it is
`pytest --env <name>`.

Resolve the choice in one place, `pytest_configure`, and expose it through the
`execution_config` fixture, so an unknown `--env` fails once at startup as a
`pytest.UsageError` (listing the available names) instead of breaking every test's setup:

```python
# conftest.py
def pytest_addoption(parser):
    # every custom option defaults to None and falls back to the config at use time,
    # so --env is what decides which environment's values are read
    parser.addoption("--env", action="store", default=None, help="a key of config/environment.json")


def pytest_configure(config):
    try:
        config.execution_config = ExecutionConfig.load(config.getoption("--env"))
    except (KeyError, FileNotFoundError, ValueError) as error:
        raise pytest.UsageError(error.args[0]) from None


@pytest.fixture(scope="session")
def execution_config(request) -> ExecutionConfig:
    return request.config.execution_config
```

Do not load the config at import time to feed option defaults: `pytest_addoption` runs
before the command line is parsed, so those defaults would come from the wrong
environment.

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
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
ENVIRONMENT_CONFIG = CONFIG_DIR / "environment.json"
EXECUTION_CONFIG = CONFIG_DIR / "execution.json"


def _read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file was not found: {path}")
    with path.open(encoding="utf-8") as config_file:
        return json.load(config_file)


@dataclass(frozen=True)
class ExecutionConfig:
    environment_name: str
    application_url: str
    api_url: str
    keycloak_url: str | None
    browser: str
    browser_channel: str | None
    headless: bool
    default_timeout_ms: int
    test_id_attribute: str
    ignore_https_errors: bool

    @classmethod
    def load(cls, environment_name: str | None = None) -> "ExecutionConfig":
        environments = _read_config(ENVIRONMENT_CONFIG)
        execution = _read_config(EXECUTION_CONFIG)

        # the run's choice (--env) wins; then the config default; one environment
        # needs no choosing at all
        name = environment_name or execution.get("environment")
        if not name:
            if len(environments) != 1:
                raise KeyError(
                    f"{ENVIRONMENT_CONFIG} defines several environments. Set "
                    f'"environment" in {EXECUTION_CONFIG} to one of: {", ".join(environments)}.'
                )
            name = next(iter(environments))
        environment = environments[name]

        for required_key in ("ui", "apiHost"):
            if not environment.get(required_key):
                raise KeyError(
                    f"'{required_key}' is missing from environment '{name}' in "
                    f"{ENVIRONMENT_CONFIG}. Set it to your application's URL."
                )

        return cls(
            environment_name=name,
            application_url=environment["ui"],
            api_url=environment["apiHost"],
            keycloak_url=environment.get("keycloakUrl"),
            browser=execution.get("browser", "chromium"),
            browser_channel=execution.get("browser_channel"),
            headless=execution.get("headless", True),
            default_timeout_ms=execution.get("default_timeout_ms", 30000),
            test_id_attribute=execution.get("test_id_attribute", "data-testid"),
            ignore_https_errors=execution.get("ignore_https_errors", False),
        )
```

One typed object merges both files, so fixtures and tests keep a single dependency
(`execution_config`) while the files stay separate on disk.

---

# Test Data

Place test data under `data`, split by role:

```text
data/
├── input_data/                 # concrete VALUES a test feeds in
│   └── credentials.json           # per-user login records (git-ignored)
├── api_payloads/               # request-body SHAPES (templates with <placeholders>)
│   ├── login.json
│   └── create_user.json
└── expected_results/           # expected values assertions compare against
    └── login.json
```

Keep the two data roles separate:

- `data/input_data/` holds concrete values a test supplies at run time (e.g. credentials).
- `data/api_payloads/` holds the request-body *shape* as a template. Values are not
  hard-coded there; they are injected via placeholders — either passed directly at the
  call site or sourced from `input_data`.

`credentials.json` maps a named key to each user record. It holds real accounts, so it
stays out of version control and is created per machine and per CI runner. The `default`
key is the account UI tests log in with; add more keys for other roles:

```json
{
  "default": { "user": "my_user", "password": "change-me" },
  "editor": { "user": "my_editor", "password": "change-me" }
}
```

Because `@parametrize` runs at import time, the helpers that feed it
(`load_credential_users()`, `load_credential_ids()`) return no cases when the file is
absent instead of breaking collection for the whole suite; anything that really needs a
user (`load_credential`, the `login_user` fixture) fails loudly with the expected path.

For truly sensitive values, prefer `.env`, CI credentials, or a secret manager and
commit `.env.example`, not `.env`.

## Payload Templating

Payload files under `api_payloads/` may contain `<placeholder>` tokens that are
substituted at load time. This keeps the request *shape* in one file while the *values*
are supplied at the call site, so the same template serves many cases.

`data/api_payloads/create_user.json` (shape only):

```json
{
  "name": "<name>",
  "email": "<email>"
}
```

Substitution happens in `load_api_payload(name, **params)` — pass the values directly:

```python
payload = load_api_payload(
    "create_user",
    name="Jane Doe",
    email="jane@example.com",
)
# -> {"name": "Jane Doe", "email": "jane@example.com"}
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
login body is also a template (`api_payloads/login.json` with `<email>` /
`<password>`) fed from `input_data/credentials.json`. If credentials were real
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
CREDENTIALS_FILE = INPUT_DATA_DIR / "credentials.json"
_PLACEHOLDER = re.compile(r"<([^<>]+)>")


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Data file was not found: {path}")
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _read_credentials() -> dict:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"No credentials file was found at {CREDENTIALS_FILE}. Create it with at "
            f'least a "default" user: {{"default": {{"user": "...", "password": "..."}}}}.'
        )
    return _read_json(CREDENTIALS_FILE)


def load_credentials() -> list[dict]:
    return list(_read_credentials().values())


def load_credential(key: str) -> dict:
    users = _read_credentials()
    if key not in users:
        raise KeyError(f"User '{key}' was not found in {CREDENTIALS_FILE}.")
    return users[key]


# the two helpers below feed @parametrize, which runs at import time: with no
# credentials file they yield no cases instead of failing collection
def load_credential_ids() -> list[str]:
    return list(_read_credentials().keys()) if CREDENTIALS_FILE.exists() else []


def load_credential_users() -> list[str]:
    return [record["user"] for record in load_credentials()] if CREDENTIALS_FILE.exists() else []


def load_passwords_by_user() -> dict[str, str]:
    return {record["user"]: record["password"] for record in load_credentials()}


def _render_placeholders(value: Any, params: dict, source: str) -> Any:
    if isinstance(value, dict):
        return {k: _render_placeholders(v, params, source) for k, v in value.items()}
    if isinstance(value, list):
        return [_render_placeholders(v, params, source) for v in value]
    if isinstance(value, str):
        exact = _PLACEHOLDER.fullmatch(value)
        if exact:
            return _lookup(exact.group(1), params, source)
        return _PLACEHOLDER.sub(lambda m: str(_lookup(m.group(1), params, source)), value)
    return value


def _lookup(token: str, params: dict, source: str) -> Any:
    if token not in params:
        raise KeyError(f"Payload '{source}' needs placeholder <{token}>, not provided.")
    return params[token]


def load_api_payload(name: str, **params: Any) -> dict:
    payload = _read_json(DATA_DIR / "api_payloads" / f"{name}.json")
    return _render_placeholders(payload, params, name)
```

## Stable Parametrize IDs

When parametrizing over records (dicts), pytest falls back to positional ids like
`user_credential0`. Provide readable ids so console output, the `[...]` node id, and
per-test artifact folders are meaningful. If the data file maps named keys to records,
expose the keys as ids via `load_credential_ids()`.

**Do not parametrize over passwords.** Allure records every test parameter and pytest
prints test arguments in tracebacks. Parametrize over the **login name** only and resolve
the password from the `user_passwords` fixture at run time:

```python
@pytest.mark.parametrize("user", load_credential_users(), ids=load_credential_ids())
def test_login(context_setup, user, user_passwords):
    user_password = user_passwords[user]
    ...
```

`ids=` accepts a list (matched to values by position) or a callable that receives each
value. `credentials.json` holds real accounts, so it stays out of version control and is
created per machine.

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

The `context_setup` fixture opens a fresh browser context and page for each test,
registers console/network listeners, navigates to the application URL (`--url`, or the
chosen environment's `ui`), and attaches failure artifacts on teardown. Page objects
receive the yielded `page` only:

```python
import pytest
from playwright.sync_api import Browser

from utils.config_reader import ExecutionConfig


@pytest.fixture(scope="function")
def context_setup(browser_setup: Browser, request, execution_config: ExecutionConfig):
    page = browser_setup.new_context().new_page()
    page.set_default_timeout(execution_config.default_timeout_ms)
    page.goto(url=request.config.getoption("--url") or execution_config.application_url)
    yield page
    # teardown: traces, screenshots, video, console/network (see Rich Failure Artifacts)
```

## API Fixture

```python
from collections.abc import Iterator

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from api.clients.auth_api import AuthApi
from utils.config_reader import ExecutionConfig


@pytest.fixture
def api_context(
    playwright: Playwright,
    execution_config: ExecutionConfig,
) -> Iterator[APIRequestContext]:
    context = playwright.request.new_context(
        base_url=execution_config.api_url,
    )

    yield context

    context.dispose()


@pytest.fixture
def auth_api(api_context: APIRequestContext) -> AuthApi:
    return AuthApi(api_context)
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
@allure.step("UI · login (user: {email})")
def login_and_continue(self, email, password) -> None:
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
UI · login (user: admin@example.com)
├── Fill 'Email' = 'admin@example.com'
├── Fill 'Password' = '***'
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

The hook above is the minimal version. This framework instead captures the screenshot in
the `context_setup` teardown, where the trace, video and browser logs are also available,
and uses `pytest_runtest_makereport` only to record each phase's result and build the
readable traceback.

## Rich Failure Artifacts

On failure, attach diagnostic evidence in one place (the `context_setup` teardown for
UI tests, or the `api_context` teardown for API-only tests), gated so passing tests
stay clean. Group attachments under four named `allure.step` sections; create a section
only when it has content:

- **Playwright trace** — trace zip plus a pointer on how to open it.
- **Automation trace code** — readable, project-scoped failure traceback.
- **UI screenshot/video** — full-page screenshot and/or execution recording.
- **Browser console/network** — console errors/warnings, page exceptions, network
  failures, and HTTP error responses.

Useful attachments within those groups:

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
    --html=reports-results/report.html --self-contained-html
    --alluredir=reports-results/allure-results
```

Default the report outputs in `addopts` so a plain `pytest` always produces them, and
leave `--tracing` / `--video` as per-run flags. Do not add `--screenshot=only-on-failure`:
that option belongs to `pytest-playwright`'s own `page` fixture, and this framework takes
its screenshot in the `context_setup` teardown instead.

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
- [ ] Passwords and tokens are external secrets; never parametrize over passwords.
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
12. Treat example page objects, API clients, and tests as template references to
    replace; do not commit product-specific values into `config/` or `data/`.
13. When modifying existing code, preserve the current naming and architecture
    unless a change is necessary and clearly explained.
