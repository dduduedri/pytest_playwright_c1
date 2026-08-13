import allure
import pytest

from ui.pages.login_page import LoginPage
from utils.data_reader import load_credential_emails, load_credential_ids


# pure UI test: log in through the browser using the page object.
# context_setup (a fixture) provides a ready page already on the app URL
@allure.epic("E-commerce")
@allure.feature("Authentication")
@allure.story("User can log in via the UI")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("UI · login · {user_email}")
@pytest.mark.ui
@pytest.mark.parametrize("user_email", load_credential_emails(), ids=load_credential_ids())
def test_login(context_setup, user_email, user_passwords):
    # resolve this run's password from the fixture. it is deliberately not a test
    # parameter: Allure records every parameter's repr(), so it would reach the report
    with allure.step("Arrange · read user credentials"):
        user_password = user_passwords[user_email]

    # drive the UI through the page object (never raw selectors in the test)
    login_page = LoginPage(context_setup)
    login_page.login_and_dashboard(user_email, user_password)
