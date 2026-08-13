import pytest
from playwright.sync_api import Playwright

from api.clients.auth_api import AuthApi
from api.clients.orders_api import OrdersApi
from utils.config_reader import ExecutionConfig
from utils.report import attach_failure_traceback, is_test_failed


# create a fresh API request context (HTTP session) bound to the api base_url.
# yield gives it to the test, then dispose() cleans it up afterwards
@pytest.fixture(scope="function")
def api_context(playwright: Playwright, execution_config: ExecutionConfig, request):
    context = playwright.request.new_context(base_url=execution_config.api_url)
    yield context

    # API-only tests have no browser context, so this is where their failure evidence
    # comes from. UI/e2e tests tear down context_setup first and attach it there; the
    # helper only attaches once per test, so nothing is duplicated here
    if is_test_failed(request.node):
        attach_failure_traceback(request.node)

    context.dispose()


# provide a ready-to-use AuthApi client wired to the request context
@pytest.fixture(scope="function")
def auth_api(api_context) -> AuthApi:
    return AuthApi(api_context)


# provide a ready-to-use OrdersApi client wired to the request context
@pytest.fixture(scope="function")
def orders_api(api_context) -> OrdersApi:
    return OrdersApi(api_context)
