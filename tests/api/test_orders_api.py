import allure
import pytest

from api.clients.orders_api import OrdersApi
from utils.data_reader import load_credential_emails, load_credential_ids


# pure API test: create an order through the API client (no browser involved).
# @parametrize runs it once per user in credentials.json; orders_api is injected by a fixture
@allure.epic("E-commerce")
@allure.feature("Orders API")
@allure.story("Create order via API")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("API · create order · {user_email}")
@pytest.mark.api
@pytest.mark.parametrize("user_email", load_credential_emails(), ids=load_credential_ids())
def test_create_order_api(orders_api: OrdersApi, user_email, user_passwords):
    # call the client (which logs in, then posts the order) and get the new id.
    # the password comes from the fixture so it never becomes a report parameter
    order_id = orders_api.create_order(user_email, user_passwords[user_email])
    allure.attach(str(order_id), name="output · order id", attachment_type=allure.attachment_type.TEXT)
    # basic check that an order id was returned
    assert order_id
