import pytest

from utils.data_reader import load_credential, load_credentials, load_passwords_by_user


# session fixture: load user credentials once and share them across the run
@pytest.fixture(scope="session")
def credentials() -> list[dict]:
    return load_credentials()


# session fixture: the user the UI logs in as, taken from the "default" record of the
# credentials file. ask for a different key when a test needs another role
@pytest.fixture(scope="session")
def login_user() -> dict:
    """Return the {user, password} record of the default UI user."""
    return load_credential("default")


# session fixture: user -> password map used to resolve a password inside the test.
# allure-pytest records every test parameter as repr(value), so parametrizing over a
# credentials dict would print the password in the report; the login name is
# parametrized (it is not a secret) and the password is looked up here instead
@pytest.fixture(scope="session")
def user_passwords() -> dict[str, str]:
    """Return a {user: password} map for the users in the credentials file."""
    return load_passwords_by_user()
