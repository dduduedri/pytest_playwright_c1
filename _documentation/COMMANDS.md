# Playwright + pytest Command Notes

A quick reference of handy Playwright and pytest snippets.

> **Source:** These commands are based on the Udemy course
> [Playwright PYTHON Automation Testing - From Zero to Expert](https://www.udemy.com/course/playwright-python-automation-testing-pytest/).

## Locators

CSS locator by attribute: `#` for `id`, `.` for `class`, tag name for the element.

```text
#locator css : attribute(id) # , class . , tag
```

## Running tests

```bash
# single test in a file (headed = visible browser)
pytest -s playwrightBasics.py::test_playwright_shortcut --headed

# whole file, choosing the browser
pytest -s test_e2e_framework_web_api.py --headed --browser_name firefox
```

## Markers

```python
@pytest.mark.smoke   # group
@pytest.mark.skip    # skip test
```

## Assertions & delay

```python
expect(my_page.locator("h1")).to_have_text("Your Orders")
```

## Filtering elements

Get an element by filter:

```python
order_raw = my_page.locator("//tbody/tr").filter(has_text=order_id)
```

XPath contains text:

```text
//td/button[contains(text(), 'View')]
//div[contains(@class,'mt-4')]
```

## Child window (popup)

```python
with page.expect_popup() as new_page:
    page.locator(".blinkingText").first.click()
    child_page = new_page.value
```

## Alert box (dialog)

```python
# without lambda
def handle_dialog(dialog: Dialog):
    dialog.accept()

# page.on("dialog", handle_dialog)  # without lambda
page.on("dialog", lambda dialog: dialog.accept())  # lambda example: add = lambda a, b: a + b -> print(add(2, 3))

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

## Positional selectors

```python
# nth element
order_raw.locator("//td").nth(view_id_index).get_by_role("button", name="View").click()

# first element
order_raw.locator("//td").first.click()

# last element
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
    # replace the call request from the browser
    route.continue_(url="https://rahulshettyacademy.com/api/ecom/order/get-orders-details?id=6a61eba885b8849b49068294")

page.route("https://rahulshettyacademy.com/api/ecom/order/get-orders-details?id=*", intercept_response_not_author)
```

## Inject data into context session

```python
my_token = api_utils.get_token(playwright)
my_browser = playwright.chromium.launch(headless=False)
print(f"my_token :{my_token}")
my_context = my_browser.new_context()
my_page = my_context.new_page()
my_page.add_init_script(f"""localStorage.setItem('token', '{my_token}')""")
```

## JSON dataset (data-driven tests)

Runs the test once per record. `data/credentials/credentials.json` maps a named key to each record:

```json
{
  "user_a": { "userEmail": "...", "UserPassword": "..." },
  "user_b": { "userEmail": "...", "UserPassword": "..." }
}
```

Loaders (see `utils/data_reader.py`):

```python
def load_credentials():
    with open('data/credentials/credentials.json') as json_file:
        return list(json.load(json_file).values())   # -> [ {user_a}, {user_b} ]

def load_credential_ids():
    with open('data/credentials/credentials.json') as json_file:
        return list(json.load(json_file).keys())      # -> ["user_a", "user_b"]
```

Parametrize the test, labelling each case by its key with `ids=`:

```python
# ids= labels each case: test_e2e_api[user_a], test_e2e_api[user_b]
@pytest.mark.parametrize('user_credential', load_credentials(), ids=load_credential_ids())
# @pytest.mark.parametrize('user_credential', load_credentials(), ids=lambda user: user["userEmail"])  # label by email instead
def test_e2e_api(context_setup, user_credential):
    ...
```
