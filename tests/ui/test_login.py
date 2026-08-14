import allure
import pytest

from ui.pages.login_page import LoginPage
from utils.data_reader import load_credential_ids, load_credential_users


# EXAMPLE UI test - the reference for every UI test you add: it drives the browser
# through a page object only. context_setup (a fixture) provides a ready page
# already on the app URL.
# Remove the skip marker once LoginPage points at your application's login form.
@allure.epic("Example")
@allure.feature("Authentication")
@allure.story("User can log in via the UI")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("UI · login · {user}")
@pytest.mark.ui
@pytest.mark.skip(reason="Template example - update LoginPage for your app, then remove this marker")
@pytest.mark.parametrize("user", load_credential_users(), ids=load_credential_ids())
def test_login(context_setup, user, user_passwords):
    # resolve this run's password from the fixture. it is deliberately not a test
    # parameter: Allure records every parameter's repr(), so it would reach the report
    with allure.step("Arrange · read user credentials"):
        user_password = user_passwords[user]

    # drive the UI through the page object (never raw selectors in the test)
    login_page = LoginPage(context_setup)
    login_page.login_and_continue(user, user_password)
    login_page.verify_logged_in()
