import allure
import pytest

from api.clients.orders_api import OrdersApi
from ui.pages.login_page import LoginPage
from utils.data_reader import load_credential_emails, load_credential_ids


# end-to-end test: API creates the data (fast), then the UI verifies it.
# it uses both the orders_api client and the context_setup page fixture
@allure.epic("E-commerce")
@allure.feature("Full order lifecycle")
@allure.story("Create order (API), view it in history (UI), verify details")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Full E2E order flow · {user_email}")
@pytest.mark.e2e
@pytest.mark.full
@pytest.mark.parametrize("user_email", load_credential_emails(), ids=load_credential_ids())
def test_create_order_and_verify_ui(orders_api: OrdersApi, context_setup, user_email, user_passwords):
    # resolve this run's password from the fixture. it is deliberately not a test
    # parameter: Allure records every parameter's repr(), so it would reach the report
    with allure.step("Arrange · read user credentials"):
        user_password = user_passwords[user_email]

    # setup via API: create the order and remember its id
    order_id = orders_api.create_order(user_email, user_password)
    allure.attach(str(order_id), name="input · order id", attachment_type=allure.attachment_type.TEXT)

    # verify via UI: log in, walk to the order, and assert the confirmation message.
    # each page method returns the next page object (the "fluent" page-object flow)
    login_page = LoginPage(context_setup)
    dashboard_page = login_page.login_and_dashboard(user_email, user_password)
    order_history = dashboard_page.order_nav_link_to_history()
    order_details = order_history.select_order_from_history_and_details(order_id)
    order_details.verify_order_message()
