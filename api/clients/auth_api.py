import allure

from api.base_api import BaseApi, attach_json, attach_text
from utils.data_reader import load_api_payload

# endpoint for the login/authentication call (relative to the api base_url)
LOGIN_ENDPOINT = "/api/auth/login"


# EXAMPLE domain API client - the reference for every client you add to this template.
# Point LOGIN_ENDPOINT and the response field at your API; the structure (one class
# per business resource, HTTP helpers inherited from BaseApi) stays the same.
class AuthApi(BaseApi):

    # log in and return the auth token used to authorize later requests
    def login(self, user, password) -> str:
        with allure.step(f"API · get auth token (user: {user})"):
            # load the login body from data/api_payloads/login.json and substitute
            # its <user>/<password> placeholders with this run's credentials
            payload = load_api_payload("login", user=user, password=password)
            attach_json("request · login payload", payload)

            response = self.post(LOGIN_ENDPOINT, data=payload)

            # fail fast with a clear message if authentication did not succeed
            assert response.ok, (
                f"Login failed for {user} (status {response.status}): {response.text()}"
            )
            token = response.json()["token"]
            attach_text("output · auth token (truncated)", f"{token[:12]}…")
            return token
