import allure
import pytest

from api.clients.auth_api import AuthApi
from utils.data_reader import load_credential_ids, load_credential_users


# EXAMPLE API test - the reference for every API test you add: no browser is involved,
# the call goes through the domain client. @parametrize runs it once per user in the
# credentials file; auth_api is injected by a fixture.
# Remove the skip marker once AuthApi points at your API's login endpoint.
@allure.epic("Example")
@allure.feature("Authentication API")
@allure.story("Login returns an auth token")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("API · login · {user}")
@pytest.mark.api
@pytest.mark.skip(reason="Template example - update AuthApi for your app, then remove this marker")
@pytest.mark.parametrize("user", load_credential_users(), ids=load_credential_ids())
def test_login_returns_token(auth_api: AuthApi, user, user_passwords):
    # the password comes from the fixture so it never becomes a report parameter.
    # the client attaches the request payload and a truncated token for evidence
    token = auth_api.login(user, user_passwords[user])

    assert token, "expected an auth token in the login response"
