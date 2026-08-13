import pytest

from utils.data_reader import load_credentials, load_passwords_by_email


# session fixture: load user credentials once and share them across the run
@pytest.fixture(scope="session")
def credentials() -> list[dict]:
    return load_credentials()


# session fixture: email -> password map used to resolve a password inside the test.
# allure-pytest records every test parameter as repr(value), so parametrizing over a
# credentials dict would print the password in the report; the email is parametrized
# (it is not a secret) and the password is looked up here instead
@pytest.fixture(scope="session")
def user_passwords() -> dict[str, str]:
    return load_passwords_by_email()
