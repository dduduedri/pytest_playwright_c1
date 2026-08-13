# Pytest + Playwright Notes

## Based on Udemy course
https://amdocsglobal.udemy.com/course/playwright-python-automation-testing-pytest/

## Basic commands
### Playwright locator identifier -
playwright codegen http://rahulshettyacademy.com/client

### Run the full suite (Chrome, parallel, tracing + video, clean old Allure results)
pytest --browser_name chrome -m full -n auto --headless --tracing on --video on --clean-alluredir

### Open the Allure report
allure serve reports-results/allure-results

### Open a saved Playwright trace
playwright show-trace "reports-results/test-results/test_create_order_and_verify_ui[user_a]/trace.zip"

## Project structure

```
ui/          Browser automation: pages/, elements/, components/
api/         API automation: base_api.py, clients/, models/
tests/       Tests split into ui/, api/, e2e/
config/      execution.json (execution settings) + environments.json
data/        credentials/credentials.json, api_payloads/, expected_results/
utils/       config_reader, data_reader, logger
fixtures/    pytest fixtures (ui_fixtures, api_fixtures, data_fixtures)
conftest.py  options + reporting hook + execution_config + pytest_plugins
```

## Locators

CSS locator by attribute: `#` for `id`, `.` for `class`, tag name for element.

```
#locator css : attribute(id) # , class . , tag
```

## Running Tests

```bash
# run a single test in a file (headed = visible browser)
pytest -s playwrightBasics.py::test_playwright_shortcut --headed

# run a whole file and choose the browser
pytest -s tests/e2e/test_create_order_and_login.py --headed --browser_name firefox

# run all tests
pytest -s
```

### Run by marker

Markers are registered in `pytest.ini` (`smoke`, `full`, `ui`, `api`, `e2e`, `regression`).

```bash
pytest -m smoke        # run only smoke tests
pytest -m full         # run only full end-to-end tests
pytest -m ui           # run only UI tests
pytest -m api          # run only API tests
pytest -m "not smoke"  # run everything except smoke
```

### Custom command-line options

Defaults are loaded from `config/execution.json` via `utils/config_reader.py` (see `conftest.py`).

```bash
pytest -s --browser_name firefox   # chromium (default), firefox, or webkit
pytest -s --url http://rahulshettyacademy.com/client
```

### Run in parallel (pytest-xdist)

`pytest-xdist` distributes tests across multiple worker processes.

```bash
pytest -n auto     # use one worker per CPU core
pytest -n 3        # use 3 parallel workers
pytest -n 4        # use 4 parallel workers
```

> Tests launch real browsers, so parallel runs open multiple browser windows at once.

### HTML report (pytest-html)

`pytest-html` generates a self-contained HTML report of the run.

```bash
pytest --html=report.html --self-contained-html
```

Open `report.html` in a browser to view the results.

### Tracing (Playwright)

Tracing is wired into the `context_setup` fixture in `conftest.py`. When enabled, a trace of
each test is saved to `reports-results/test-results/<test-name>/trace.zip`.

```bash
pytest --tracing on                 # record a trace for every test
pytest --tracing retain-on-failure  # record only for failing tests
```

Full example (browser, marker, parallel, tracing, HTML report together):

```bash
pytest --browser_name chrome -m full -n auto --tracing on --html=report.html
```

#### View a trace

Option 1 - local viewer:

```bash
playwright show-trace "reports-results/test-results/<test-name>/trace.zip"
```

Option 2 - online viewer: open [trace.playwright.dev](https://trace.playwright.dev/) and
drag-and-drop the `trace.zip` file onto the page (the file is processed locally in your
browser and is not uploaded anywhere).

### Run by partial name

`-k` selects tests whose name matches an expression (substring match).

```bash
pytest -k create              # run tests whose name contains "create"
pytest -k order               # run tests whose name contains "order"
pytest -k "create or full"    # combine with or / and / not
```

### Useful flags

```bash
pytest --co -q         # collect-only: list tests without running them
pytest -m full --co    # preview which tests a marker selects
pytest --markers       # show all registered markers
```

## Markers

```python
@pytest.mark.smoke  # group
@pytest.mark.skip   # skip test
```

## Assertions & Delay

```python
expect(my_page.locator("h1")).to_have_text("Your Orders")
```

## Filtering Elements

Get element by filter:

```python
order_raw = my_page.locator("//tbody/tr").filter(has_text=order_id)
```

XPath contains text:

```
//td/button[contains(text(), 'View')]
//div[contains(@class,'mt-4')]
```

## Child Window (Popup)

```python
with page.expect_popup() as new_page:
    page.locator(".blinkingText").first.click()
    child_page = new_page.value
```

## Alert Box (Dialog)

```python
# without lambda
def handle_dialog(dialog: Dialog):
    dialog.accept()

# page.on("dialog", handle_dialog)  # without lambda

# lambda example: add = lambda a, b: a + b  ->  print(add(2, 3))
page.on("dialog", lambda dialog: dialog.accept())

# opens the dialog; Playwright automatically listens and confirms it
page.get_by_role("button", name="Confirm").click()
time.sleep(3)
```

## Tables

```python
for col_index in range(page.locator("th").count()):
    if page.locator("th").nth(col_index).filter(has_text="Price").count() > 0:
        price_col_index = col_index
        print(f"price col index : {price_col_index}")
        break

rice_row = page.locator("tr").filter(has_text="Rice")

expect(rice_row.locator("td").nth(price_col_index)).to_contain_text("37")
```

## Positional Selectors

nth element:

```python
order_raw.locator("//td").nth(view_id_index).get_by_role("button", name="View").click()
```

first element:

```python
order_raw.locator("//td").first.click()
```

last element:

```python
order_raw.locator("//td").last.click()
```

## API

Payloads:

```python
orders_payload = {"orders": [{"country": "India", "productOrderedId": "6960eac0c941646b7a8b3e68"}]}
login_payload = {"userEmail": "rahulshetty@gmail.com", "userPassword": "Iamking@000"}
```

Utility class:

```python
class APIUtils:
    def get_token(self, playwright: Playwright):
        api_request_context = playwright.request.new_context(base_url="https://rahulshettyacademy.com")

        response = api_request_context.post(
            "/api/ecom/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/json"},
        )
        # print(response.status)
        # print(response.text())
        assert response.ok
        response_body = response.json()
        return response_body["token"]

    def create_order(self, playwright: Playwright):
        api_request_context = playwright.request.new_context(base_url="https://rahulshettyacademy.com")
        response = api_request_context.post(
            "/api/ecom/order/create-order",
            data=orders_payload,
            headers={
                "Authorization": self.get_token(playwright),
                "Content-Type": "application/json",
            },
        )
        return response.json()["orders"][0]
```

In test:

```python
api_util = APIUtils()
print(f"token :{api_util.get_token(playwright)}")
order_id = api_util.create_order(playwright)
```

## Mocking

Fulfill (server response):

```python
fake_payload_order_response = {"data": [], "message": "No Orders"}

def intercept_response(route):
    route.fulfill(json=fake_payload_order_response)

page.route("https://rahulshettyacademy.com/api/ecom/order/get-orders-for-customer/*", intercept_response)
```

Continue (client request):

```python
def intercept_response_not_author(route):
    # replace the call request from browser
    route.continue_(url="https://rahulshettyacademy.com/api/ecom/order/get-orders-details?id=6a61eba885b8849b49068294")

page.route("https://rahulshettyacademy.com/api/ecom/order/get-orders-details?id=*", intercept_response_not_author)
```

## Inject Data into Context Session

```python
my_token = api_utils.get_token(playwright)
my_browser = playwright.chromium.launch(headless=False)
print(f"my_token :{my_token}")
my_context = my_browser.new_context()
my_page = my_context.new_page()
my_page.add_init_script(f"""localStorage.setItem('token', '{my_token}')""")
```

## JSON Dataset (Data-Driven Tests)

Runs the test once per record. `data/credentials/credentials.json` maps a **named key**
to each record:

```json
{
  "user_a": { "userEmail": "a@example.com", "UserPassword": "***" },
  "user_b": { "userEmail": "b@example.com", "UserPassword": "***" }
}
```

The project loads it via `utils/data_reader.py`:

```python
# utils/data_reader.py
def load_credentials() -> list[dict]:
    return list(_read_json(CREDENTIALS_FILE).values())   # -> [ {user_a}, {user_b} ]

def load_credential_ids() -> list[str]:
    return list(_read_json(CREDENTIALS_FILE).keys())      # -> ["user_a", "user_b"]
```

Then parametrize the test, labelling each case by its key (`ids=`):

```python
from utils.data_reader import load_credential_ids, load_credentials

# ids= gives each case a readable node id: test_login[user_a], test_login[user_b]
@pytest.mark.parametrize("user_credential", load_credentials(), ids=load_credential_ids())
def test_login(context_setup, user_credential):
    ...
```

`ids=` accepts a **list** (matched to values by position) or a **callable** that receives
each value — e.g. `ids=lambda user: user["userEmail"]` would label cases by email instead.
