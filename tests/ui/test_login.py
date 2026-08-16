import allure
import pytest

from ui.components.hamburger_menu import HamburgerMenu
from ui.pages.keycloak_login_page import KeycloakLoginPage
from utils.data_reader import load_credential_ids, load_credential_users


@allure.epic("Catalog One")
@allure.feature("Authentication")
@allure.story("User can log in via the UI")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("UI · login · {user}")
@pytest.mark.ui
@pytest.mark.parametrize("user", load_credential_users(), ids=load_credential_ids())
def test_login(context_setup, user, user_passwords, execution_config):
    # resolve this run's password from the fixture. it is deliberately not a test
    # parameter: Allure records every parameter's repr(), so it would reach the report
    with allure.step("Arrange · read user credentials"):
        user_password = user_passwords[user]

    # context_setup already opened the app URL; anonymous visitors are redirected to
    # Keycloak, so the identity-provider page is what we drive here
    KeycloakLoginPage(context_setup).sign_in(user, user_password)
    # the hamburger menu only renders for an authenticated user
    HamburgerMenu(context_setup).verify_available(timeout=execution_config.default_timeout_ms)
