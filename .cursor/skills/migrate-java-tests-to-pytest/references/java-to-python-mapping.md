# Java/TestNG -> Python/pytest translation tables

Source layout (`c1-playwright-automation-old-framework/src/main/java/com/`):

| Java package | Contents | Target |
|---|---|---|
| `testFlows/` | 48 test classes, ~119 `@Test` methods, `BaseTest` (3196 lines), `BaseApiTest` | `tests/ui`, `tests/api`, `tests/e2e` + fixtures |
| `ui/base/baseElements/` | 12 element wrappers | `ui/elements/` |
| `ui/pages/` | ~83 page/panel classes, `BasePage`, `PageFactory` | `ui/pages/` (factory dropped) |
| `ui/steps/` | ~37 step classes, `StepFactory` | folded into pages, or `ui/flows/` |
| `api/apiExecuter/`, `api/steps/`, `api/entities/` | REST Assured executor, 10 step classes, 31 entities | `api/base_api.py` (exists), `api/clients/`, `api/models/` |
| `infrastructure/` | browser manager, ConfigManager, listeners | `conftest.py` + `fixtures/` + `utils/config_reader.py` |
| `data/` | 95 enum/constant classes | `data/input_data/*.json`, small constants module |
| `utils/allure/`, `utils/wait/`, `utils/logging/` | Allure post-processing, WaitUtils, TestLogger | allure-pytest + `utils/report.py` + `utils/logger.py` |
| `resources/payloads/**` | 339 Postman-style JSON files | `data/api_payloads/**` |

---

## 1. Test layer

### Class and lifecycle

| Java | Python |
|---|---|
| `class SmokeTests extends BaseTest` | module `tests/ui/test_<feature>.py`; no base class |
| `@BeforeSuite setUpSuite` | session fixtures (`browser_setup`) |
| `@BeforeMethod setUp` (context + page) | `context_setup` fixture (already in `fixtures/ui_fixtures.py`) |
| `@BeforeMethod login` (UI login every test) | `logged_in_page` fixture wrapping `context_setup` |
| `@AfterMethod tearDown` (screenshot/video) | `context_setup` teardown (already implemented) |
| `extends BaseApiTest` (no browser) | test takes `auth_api` / `api_context` only, no `context_setup` |
| `ThreadLocal<Page>` + `parallel=methods` | process isolation via `pytest -n <N>`; no thread-locals |
| `PlaywrightManager`, `BrowserLauncher` | `fixtures/ui_fixtures.py` |
| `getPageFactory().homePage()` | `HomePage(context_setup)` |
| `stepFactory().uiCommonSteps()` | the page object or a `ui/flows/` function |
| `getCurrentTestName()` | `request.node.name` |

### Annotations

| Java | Python |
|---|---|
| `@Test(groups = {"SmokeTest","ui_SmokeTest"})` | `@pytest.mark.ui` + `@pytest.mark.smoke` + `@allure.tag("SmokeTest")` |
| `@Test(groups = {"regression_5_api"})` | `@pytest.mark.api` + `@pytest.mark.regression` + `@allure.tag("regression_5_api")` |
| `@Test(description = "NGMEC-25963 Navigate through the menu options")` | `@allure.title("NGMEC-25963 · navigate through the menu options")` + `@allure.issue("NGMEC-25963")` |
| `@Step("Navigate through the menu options")` on the test | `@allure.title(...)` (a test-level `@Step` is just the report title) |
| `@Test(retryAnalyzer = RetryAnalyzer.class)` | nothing per test; `--reruns N` in CI if parity is required |
| `@Test(priority = 1)` | ordering is not ported; make the test independent |
| `@Test(dataProvider = "controlsMenu")` + `@DataProvider` | `@pytest.mark.parametrize(..., ids=[...])` |
| `@Test(alwaysRun = true)` on a login helper | that is a fixture, not a test |
| no `@Epic/@Feature/@Story` in Java | add them: `@allure.epic(<domain>)`, `@allure.feature(<area>)`, `@allure.story(<behavior>)` |

Group -> marker mapping rule: markers stay a small closed set (`ui`, `api`,
`e2e`, `smoke`, `regression`, `sanity`) registered in `pytest.ini`; the exact
legacy group name is preserved as `@allure.tag(...)` so nothing is lost. The tag
aliases in `resources/testTag/testsTag.yaml` (`smoke`, `sanity`, `regression`,
`full`, ...) become marker expressions: `-Dtag=sanity` -> `pytest -m sanity`.

### Naming

| Java | Python |
|---|---|
| `SmokeTests#navigateThroughTheMenuOptions` | `tests/ui/test_navigation.py::test_navigate_through_the_menu_options` |
| `PriceGroupApiTests#priceGroupSupportVersioningCreateUpdateAndRemoveAPI` | `tests/api/test_price_group_api.py::test_price_group_versioning_create_update_remove` |
| `PriceCapabilities#priceRateChangeInSPOEffectBPO` | `tests/e2e/test_price_capabilities.py::test_price_rate_change_in_spo_affects_bpo` |

camelCase -> snake_case; drop the `API`/`UI` suffix (the folder and marker say
it); one Java test class -> one Python module unless the class mixes unrelated
features.

### Assertions and waiting

| Java | Python |
|---|---|
| `Assert.assertEquals(a, b)` | `assert a == b, "<message>"` |
| `assertThat(x).isTrue()` | `assert x, "<message>"` |
| `WaitUtils.retry(() -> assertThat(page...isVisible()).isTrue(), UI_ACTION_TIMEOUT)` | `expect(locator).to_be_visible()` - web-first assertion, auto-retrying |
| `WaitUtils.retry(supplier, timeout, iterations)` returning a value | `expect(...)` on the observable state; only if truly unobservable, poll with `locator.wait_for` |
| `WaitUtils.sleep(500)` / `Thread.sleep` | delete; if a React field needs settling, assert the field value instead |
| `locator.waitFor(state)` | `locator.wait_for(state="visible")` |
| `PageValidator.validatePage(page, ...)` | not needed; pytest gives each test its own context |
| `TestExecutionTracker`, `RetryContext` | not ported |

### Test data generation

`com.data.TestDataGenerator` -> `utils/test_data.py`:

```python
from datetime import datetime, timedelta
from uuid import uuid4

def generate_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def unique_name(prefix: str) -> str:
    # the Java version is timestamp-only; the suffix keeps parallel runs unique
    return f"{prefix}_{generate_timestamp()}_{uuid4().hex[:4]}"

def due_date(days_from_now: int = 30) -> datetime:
    return datetime.now() + timedelta(days=days_from_now)
```

---

## 2. UI elements

Java `BaseElement(Page page, String selector)` builds its own locator from a
selector string. Python `BaseElement(locator, name)` receives a ready locator
and a report name: **the locator is built in the page object**, the element only
adds behavior and Allure substeps.

```java
// Java page object
new CheckBox(page, "xpath=//div[@data-test-text='" + type + "']//div[contains(@class,'checkbox-control')]").check();
```

```python
# Python page object
self.item_type = Checkbox(
    page.locator(f"xpath=//div[@data-test-text='{item_type}']//div[contains(@class,'checkbox-control')]"),
    f"catalog item type: {item_type}",
)
self.item_type.check()
```

| Java element | Python | Notes |
|---|---|---|
| `Button` (`click`, `getText`, `isEnabled`, `doubleClick`, `clickFirst`) | `ui/elements/button.py` | `clickFirst()` -> `locator.first`; drop the Java retry loop (Playwright auto-waits) |
| `TextBox` (16 methods incl. `setText`, `clearAndSetText`, `setTextAndEnter`, `setTextWithHumanSpeed`) | `ui/elements/text_box.py` | `setText` -> `fill`; `sendKey` -> `press`; `setTextAndEnter` -> `fill` + `press("Enter")`; `setTextWithHumanSpeed` -> `press_sequentially`; always `mask=True` for secrets |
| `CheckBox` (class-based `isChecked`) | `ui/elements/checkbox.py` | keep the **class-attribute** check (`"checked" in locator.get_attribute("class")`); the app is not a native `<input>` |
| `Dropdown` (`selectOption`, `searchValue`, `selectExactValueFromExpandedList`) | `ui/elements/listbox_dropdown.py` (migrated) | the app's dropdowns are not `<select>`: the control opens a page-level `role=listbox`, which the page object passes in as `options`. `ui/elements/dropdown.py` stays for real `<select>` elements |
| `Link` | `ui/elements/link.py` (migrated) | second ctor overload (`selector` + text) -> pass `locator.get_by_text(text)` from the page |
| `RadioButton` (`select`, `isSelected` via `active` class) | add `ui/elements/radio_button.py` | keep class/aria check |
| `ToggleButton` (`toggleOn/Off`, `Toggle` enum) | add `ui/elements/toggle_button.py` | Java `toggleOff()` never clicks - fix it, do not copy the bug |
| `Collapsible`, `InfoIcon` | add when needed | thin wrappers over the nested icon locator |
| `DatePicker` | `ui/elements/date_picker.py` (migrated) | the calendar popup renders outside the field, so the page object passes the popup's Apply button in; keep Java's page-global `get_by_text("Apply", exact=True).first` - the popup is not a child of the field. `choose_day_label()` rebuilds `getCurrentDateOption()`'s label |
| `VerticalDots` (three-dot menu) | add `ui/elements/vertical_dots.py` | menu items via `get_by_role`/`get_by_test_id`, not embedded-text XPath, when possible |

Only add an element class when a migrated page actually uses it.

---

## 3. Pages, and the death of the steps layer

| Java | Python |
|---|---|
| `BasePage(Page page)` with `locate()`, `pageLocator()`, `hoverAtCenter()` | `ui/pages/base_page.py` stays minimal; use Playwright locators directly |
| `AllureStepWrapper.step("name", page, locator, () -> ...)` | `with allure.step("name"):` or `@allure.step` on the page method |
| page method returning `void` | return the next page object when the app navigates, so tests chain |
| `PageFactory` (~80 lazy getters) | delete; construct pages where needed |
| `StepFactory` (~37 getters) | delete |
| `UICommonSteps` (119 methods) | split across the pages it drives; never one `common_steps.py` |
| step method that calls one page | a method on that page object (`verify_*` if it asserts) |
| step method that drives 2+ pages | `ui/flows/<domain>_flow.py` function taking `page` and returning nothing |
| `Calendar` page (66 methods) vs `DatePicker` element | keep the same split: page-level calendar stays a page/component |

Worked example - Java three layers collapse to two:

```java
// steps
@Step("Open Search Catalog from home")
public void openSearchCatalog() {
    openHomePageAndAssert();
    pageFactory.homePage().clickSearchCatalog();
    retry(() -> assertThat(pageFactory.searchCatalogPanel().isGlobalSearchPanelOpen()).isTrue(), UI_ACTION_TIMEOUT);
}
```

```python
# ui/flows/search_flow.py - it spans two pages, so it is a flow
import allure
from ui.pages.home_page import HomePage
from ui.pages.search_catalog_panel import SearchCatalogPanel


def open_search_catalog(page) -> SearchCatalogPanel:
    with allure.step("UI · open Search Catalog from home"):
        HomePage(page).verify_loaded().click_search_catalog()
        panel = SearchCatalogPanel(page)
        panel.verify_open()
        return panel
```

### Locators

The legacy UI is `data-test-id` / `data-test-text` driven, mostly through XPath.

| Java | Python |
|---|---|
| `"[data-test-id='home-page-create-business-request']"` | `page.get_by_test_id("home-page-create-business-request")` (needs `set_test_id_attribute("data-test-id")`) |
| `"[data-test-id='" + brId + "'] div.status-indicator-label"` | `page.get_by_test_id(br_id).locator("div.status-indicator-label")` |
| `"xpath=//div[@role='listbox']"` | `page.get_by_role("listbox")` |
| `"xpath=//label[@data-test-id='sign-in'] \| //input[@id='kc-login']"` | prefer `get_by_role("button", name="Sign in")`; keep the XPath union only if the app really needs it |
| complex domain XPath with `contains(@class, ...)` | keep verbatim: `page.locator("xpath=//...")` |
| `xpathQuote()` helper for `'` escaping | same need; keep a small helper if the slice uses it |
| Java appends `.first()` on `contains()` locators | `locator.first` - keep this everywhere the Java code had it |

Priority: `get_by_test_id` > `get_by_role` > `get_by_label` > CSS > XPath. Do
**not** add container scoping the Java locator did not have, and do not
"improve" a column index into a name lookup - the legacy grid is virtualized.

---

## 4. API layer

### Executor

| Java | Python |
|---|---|
| REST Assured `given().header().body().post(url)` | `BaseApi.post(endpoint, data=payload)` over `APIRequestContext` |
| `ApiExecutor.run(fullRequestFilePath, values)` | a method on a domain client |
| Postman envelope `*_full.json` (method + url + headers + `{{token}}`) | endpoint constant + `self.post(...)` in the client; the envelope file is not ported |
| body template `*_body.json` (map of escaped JSON strings) | one payload file per request: `data/api_payloads/<domain>/<request>.json` |
| `{{brName}}` placeholder | `<br_name>` placeholder, substituted by `load_api_payload("...", br_name=...)` |
| `rawBodyValue` escaping trick | not needed; the payload is a real JSON object |
| `requestValues.put("server", ConfigManager.getApiServer())` | `api_url` base_url on the request context |
| `requestValues.put("token", "Bearer " + token)` | `headers={"Authorization": f"Bearer {token}"}` |
| `validateResponseStatus(response, Set.of(200,201))` | `assert response.status in (200, 201), "<domain message>"` in the client |
| `attachToAllure()` request/response | already in `BaseApi._attach_response` + `attach_json` (masks secrets) |
| `getLastRequestUrl/StatusCode()` | not needed |
| relaxed SSL, cleared proxy | `playwright.request.new_context(ignore_https_errors=True)` if required |

### Steps and entities

| Java | Python |
|---|---|
| `GenericApiSteps` (62 methods), `EntitySearchApiSteps` (37) | split by domain: `api/clients/business_request_api.py`, `entity_search_api.py`, ... |
| `ApiStepFactory` | one pytest fixture per client in `fixtures/api_fixtures.py` |
| `BaseApiEntity.apiRun(...)` | `self.post(...)` / `self.get(...)` from `BaseApi` |
| active-record entity (`BusinessRequest` with 98 methods) | a client method per operation; keep a thin `api/models/business_request.py` (id + client) only if tests chain `br.publish()` |
| `EntityTracker.trackEntity(...)` | cleanup in the fixture teardown, or an explicit delete call |
| `@Step` on every API step method | `with allure.step(...)` / `@allure.step` on the client method |
| `WaitUtils.retry` around a search assertion | poll the API in the client with an explicit deadline, or assert on the UI with `expect` |

### Auth

Keycloak resource-owner password grant, client id `apigw`, endpoint
`{keycloak_url}/protocol/openid-connect/token`, form params `grant_type`,
`client_id`, `username`, `password`:

```python
class AuthApi(BaseApi):
    def get_token(self, username: str, password: str) -> str:
        with allure.step(f"API · get Keycloak token (user: {username})"):
            response = self.request_context.post(
                f"{self.keycloak_url}/protocol/openid-connect/token",
                form={
                    "grant_type": "password",
                    "client_id": "apigw",
                    "username": username,
                    "password": password,
                },
            )
            assert response.ok, f"token request failed ({response.status})"
            return response.json()["access_token"]
```

Token caching: a session-scoped fixture per user key (Java caches per thread and
refreshes near expiry). `AsmTokenManager` (A3S/`subjectToken`) becomes a second
small client used only by the tests that need it. Never log or attach a token
beyond a truncated prefix.

---

## 5. Configuration keys

`environment/envInfo.yaml` + generated `envExecInfo.yaml` -> `config/environment.json`
(migrated). The legacy file keeps one active environment and comments the rest out; the
Python file keeps them all, keyed by `env_name`, and `execution.json: environment` picks
one. **The service keys keep their Java names** so an environment block can be copied
across verbatim; `utils/config_reader.py` maps them onto the typed fields:

| `environment.json` key | `ExecutionConfig` field |
|---|---|
| the entry's key (`env_name`) | `environment_name` |
| `ui` (required) | `application_url` |
| `apiHost` (required) | `api_url` |
| `keycloakUrl` | `keycloak_url` |
| `a3sUrl` | `asm_url` |
| `posUrl` | `pos_url` |
| `dashboardUrl` | add when a migrated test needs it |

`properties/playwright.properties` -> `config/execution.json` or CLI:

| Java property | Python |
|---|---|
| `browser.name` | `execution.json: browser` |
| `browser.headless` | `execution.json: headless` (+ `--headed` / `--headless`) |
| `browser.ignore.https.errors` | `execution.json: ignore_https_errors`. Like the Java `BrowserLauncher`, it is applied twice: `new_context(ignore_https_errors=...)` and the `--ignore-certificate-errors` launch arg. The OCP environments serve an internal certificate, so without it `page.goto` fails with `ERR_CERT_AUTHORITY_INVALID` |
| `browser.performance.flags`, `--disable-blink-features=AutomationControlled`, `--remote-debugging-port=0`, `--no-first-run`, ... | not ported: Playwright already isolates each context, and these tuned the Java suite's parallel windows |
| `proxy.clear.settings`, `proxy.no.proxy` | applies to REST Assured only (JVM proxy properties + `NO_PROXY`), i.e. **API calls go direct, never through the corporate proxy**. Port it with the first API slice (the browser side is left to the machine's own proxy configuration, exactly as in Java) |
| `browser.use.custom.path`, `browser.custom.path`, vendored chromium | dropped: `playwright install` |
| `test.timeout.default` | `execution.json: default_timeout_ms` |
| `test.timeout.element.wait`, `test.timeout.click` | per-call `timeout=` or `expect.set_options`; add to `execution.json` only if used |
| `UI_ACTION_ITERATION_TIMEOUT`, `API_ACTION_ITERATION_TIMEOUT` | not ported (web-first assertions replace retry loops) |
| `BR_VALIDATION_TIMEOUT_SEC`, `BR_PUBLISH_TIMEOUT_SEC`, `PUBLISH_BR_FLAG` | `execution.json` domain settings |
| `video.recording.*` | `--video on|retain-on-failure` |
| `code.trace.enabled` | replaced by the pretty traceback in `conftest.py` |
| `test.retry.count` | `--reruns` (only if adopted) |
| `test.parallel`, `test.thread.count` | `-n <N>` (pytest-xdist) |
| `cleanup.*`, `allure.*` paths | `pytest.ini` addopts + `--clean-alluredir` hook |
| `nexus.*`, `remote.server.*`, couchbase hosts | out of scope unless the user asks |
| `users/users.yaml` (`default`, `UserA`, `Editor`, ...) | `data/input_data/credentials.json` (git-ignored) keyed `default`, `user_a`, `editor`, ... with `user`/`password`, mirroring the Java `userName`/`password` record; `default` is the account the `logged_in_page` fixture signs in with. Port only the users a migrated test needs |

Execution command equivalence:

| Java | Python |
|---|---|
| `mvn clean test -Dgroups=SmokeTest` | `pytest -m smoke` |
| `mvn clean test -Dtag=sanity` | `pytest -m sanity` |
| `mvn clean test -Dtest=createBR` | `pytest -k create_br` |
| `./run.sh -Run '#createBR' -EnvName '<env>'` | `pytest -k create_br --env <env>` (the `-EnvName` equivalent: `--env` takes a key of `environment.json`) |
| `-DthreadCount=4 -Dparallel=methods` | `-n 4` |
| `-Dbrowser.headless=true` | `--headless` |

---

## 6. Data classes (95 files in `com/data/`)

| Java kind | Example | Target |
|---|---|---|
| entity/API slug enums | `EntityType.CREATE_A_PRICE_GROUP("pricegroup")` | `data/input_data/entity_types.json` + plain strings |
| UI label/status enums | `BusinessRequestStatus.READY_FOR_PUBLISH("Ready for Publish")` | `data/input_data/ui_labels.json` |
| catalog baseline names + ids | `SimpleProductOfferName.MOBILE_EXTRA_PLAN` + `_ID` | `data/input_data/catalog_entities.json` (env-specific ids: note it) |
| characteristic labels (UI + API spelling) | `CharacteristicsDataNames.PLAN_TYPE_WITH_UNDERSCORE` | `data/input_data/characteristics.json` |
| expected messages | `ValidationMessage`, `AutoFixMessage` | `data/expected_results/validation_messages.json` |
| excel sheet/column names | `ProductOfferingExcelData` | `data/expected_results/<export>.json` |
| import zip registry | `ZipFiles` enum | `data/input_data/import_files.json` |
| framework constants | `Constants.SUCCESS_STATUS_CODES` | Python constants next to their user |
| query fragments | `CouchbaseQuery` | out of scope |
| runtime flags | `UITestGlobalConfiguration.ADVANCED_CHAR_VALUE_SELECTION` | `config/execution.json` |
| `@NotImplementedInUI` annotation | dropped |

Enum-typed method parameters (`CatalogItemType`, `EntityType`,
`BusinessRequestType`) become `str` values loaded from JSON. If a slice needs
type safety, use `typing.Literal` at the boundary - do not recreate Java enums.

---

## 7. Allure parity

| Legacy capability | Target |
|---|---|
| `@Step` on tests / steps / API methods | `@allure.title`, `@allure.step`, `with allure.step` |
| `AllureStepWrapper` step params (locator, status) | `allure.attach` / step titles |
| failure screenshot (test + step) | `context_setup` teardown (implemented) |
| video attachment | `--video`, attached in teardown (implemented) |
| Java "code trace" HTML (JavaParser) | project-scoped pretty traceback (implemented) |
| API request/response attachments | `BaseApi` + `attach_json` with secret masking (implemented) |
| env info attachment per test | one session-scoped `environment.properties` / attachment |
| suite organizer, historyId partitioning | allure labels/markers; drop the custom partitioning |
| retry reconciliation, attempt totals | drop |
| thread timeline report | drop |
| Playwright trace / HAR | **new capability** - already in the target (`--tracing`) |

Do not rebuild `AllureReportManager` (2074 lines) or `AllureJsonUpdater`. The
only post-processing the target keeps is the "Unknown fixture rows" cleanup in
`pytest_sessionfinish`.

---

## 8. Out of scope by default

Flag these, get a decision, and record them in the ledger's out-of-scope list
rather than silently dropping the tests that use them:

Couchbase N1QL via SSH/curl (`CouchbaseSteps`, `couchbase_hosts.yaml`), OCP
route discovery over SSH (`ElasticSearchSteps`), Nexus artifact download,
Docker/Helm/Jenkins distributed execution, vendored browser download,
`browser.keep.open.after.test` debug latch, thread activity reporting,
`CleanupManager`, and the `../E2E` resource overlay.

Migratable but needing work: multipart catalog import (`CatalogImportClient` ->
`APIRequestContext` multipart), Excel validation of downloaded exports
(`XLUtil` -> `openpyxl`), and dashboard calls that reuse the browser session
cookie (`DashboardApi` -> pass `context.cookies()` into the API context).
