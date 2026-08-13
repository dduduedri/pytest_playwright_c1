import allure
import pytest

from api.clients.orders_api import OrdersApi
from ui.pages.login_page import LoginPage
from utils.data_reader import load_credential_emails, load_credential_ids


# smoke e2e test: create an order via API, then confirm login works via UI.
# marked 'smoke' so it can be run quickly with `pytest -m smoke`
@allure.epic("E-commerce")
@allure.feature("Order creation")
@allure.story("Create order via API, then log in via UI")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Smoke · create order (API) + login (UI) · {user_email}")
@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.parametrize("user_email", load_credential_emails(), ids=load_credential_ids())
def test_create_order_and_login(orders_api: OrdersApi, context_setup, user_email, user_passwords):
    # resolve this run's password from the fixture. it is deliberately not a test
    # parameter: Allure records every parameter's repr(), so it would reach the report
    with allure.step("Arrange · read user credentials"):
        user_password = user_passwords[user_email]

    # setup via API: create the order
    order_id = orders_api.create_order(user_email, user_password)
    allure.attach(str(order_id), name="input · order id", attachment_type=allure.attachment_type.TEXT)

    # verify via UI: the same user can log in and reach the dashboard
    login_page = LoginPage(context_setup)
    login_page.login_and_dashboard(user_email, user_password)
