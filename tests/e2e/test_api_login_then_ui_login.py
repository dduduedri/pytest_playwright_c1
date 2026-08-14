import allure
import pytest

from api.clients.auth_api import AuthApi
from ui.pages.login_page import LoginPage
from utils.data_reader import load_credential_ids, load_credential_users


# EXAMPLE end-to-end test - the reference for every e2e test you add: the API does the
# fast setup, the UI verifies only what really needs a browser. It uses both an API
# client and the context_setup page fixture.
# Remove the skip marker once AuthApi and LoginPage point at your application.
@allure.epic("Example")
@allure.feature("Authentication")
@allure.story("Authenticate via API, then verify login through the UI")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("E2E · API login + UI login · {user}")
@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.skip(reason="Template example - update AuthApi and LoginPage for your app, then remove this marker")
@pytest.mark.parametrize("user", load_credential_users(), ids=load_credential_ids())
def test_api_login_then_ui_login(auth_api: AuthApi, context_setup, user, user_passwords):
    # resolve this run's password from the fixture. it is deliberately not a test
    # parameter: Allure records every parameter's repr(), so it would reach the report
    with allure.step("Arrange · read user credentials"):
        user_password = user_passwords[user]

    # setup via API: this is where a real test would create the data it needs
    # (and hand the token to further API calls)
    token = auth_api.login(user, user_password)
    assert token, "expected an auth token before driving the UI"

    # verify via UI through page objects; a page method returns the next page object,
    # so flows read as a chain once you add more pages
    login_page = LoginPage(context_setup)
    login_page.login_and_continue(user, user_password)
    login_page.verify_logged_in()
