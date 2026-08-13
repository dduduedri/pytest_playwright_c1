import allure

from api.base_api import BaseApi, attach_json, attach_text
from api.clients.auth_api import AuthApi
from utils.data_reader import load_api_payload

# endpoint for creating an order (relative to the api base_url)
CREATE_ORDER_ENDPOINT = "/api/ecom/order/create-order"


# domain API client for orders; inherits HTTP helpers from BaseApi
class OrdersApi(BaseApi):

    # create an order for the given user and return the new order id
    def create_order(self, user_email, user_password) -> str:
        with allure.step("API · create order"):
            # authenticate first to obtain the token needed for authorization
            token = AuthApi(self.request_context).login(user_email, user_password)

            # substitute the order values directly into the <placeholder> tokens
            # in create_order.json (values passed here at the call site)
            payload = load_api_payload(
                "create_order",
                country="India",
                productOrderedId="6960eac0c941646b7a8b3e68",
            )
            attach_json("request · create-order payload", payload)

            response = self.post(CREATE_ORDER_ENDPOINT, data=payload, headers={"Authorization": token})

            order_id = response.json()["orders"][0]
            attach_text("output · created order id", order_id)
            return order_id
