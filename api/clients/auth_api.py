import allure

from api.base_api import BaseApi, attach_json, attach_text
from utils.data_reader import load_api_payload

# endpoint for the login/authentication call (relative to the api base_url)
LOGIN_ENDPOINT = "/api/ecom/auth/login"


# domain API client for authentication; inherits HTTP helpers from BaseApi
class AuthApi(BaseApi):

    # log in and return the auth token used to authorize later requests
    def login(self, user_email, user_password) -> str:
        with allure.step(f"API · get auth token (user: {user_email})"):
            # load the login body from data/api_payloads/login.json and substitute
            # its <userEmail>/<userPassword> placeholders with this run's credentials
            payload = load_api_payload(
                "login", userEmail=user_email, userPassword=user_password
            )
            attach_json("request · login payload", payload)

            response = self.post(LOGIN_ENDPOINT, data=payload)

            # fail fast with a clear message if authentication did not succeed
            assert response.ok, (
                f"Login failed for {user_email} (status {response.status}): {response.text()}"
            )
            token = response.json()["token"]
            attach_text("output · auth token (truncated)", f"{token[:12]}…")
            return token
