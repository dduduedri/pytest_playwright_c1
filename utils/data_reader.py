from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# resolve the data/ folder relative to the project root (cwd-independent)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


# private helper: read and parse a JSON file, with a clear error if it's missing
def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Data file was not found: {path}")
    with path.open(encoding="utf-8") as data_file:
        return json.load(data_file)


# folder holding test-input datasets (credentials, ...)
INPUT_DATA_DIR = DATA_DIR / "input_data"

# users live in credentials.json, which is git-ignored: it holds real accounts, so it
# is created per machine (see README) and never committed
CREDENTIALS_FILE = INPUT_DATA_DIR / "credentials.json"


# private helper: read the credentials file, explaining how to create it if it is absent
def _read_credentials() -> dict:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"No credentials file was found at {CREDENTIALS_FILE}. Create it with at "
            f'least a "default" user: {{"default": {{"user": "...", "password": "..."}}}}.'
        )
    return _read_json(CREDENTIALS_FILE)


# return the user credential records from the credentials file.
# the file maps a user key (default, editor, ...) to a {user, password} record;
# we return just the records as a flat list so tests can @parametrize over them
def load_credentials() -> list[dict]:
    """Return the list of user credential records from data/input_data/credentials.json."""
    return list(_read_credentials().values())


# return one credential record by its key, so a fixture can ask for a specific user
# (the login user, an editor, a reader, ...) instead of relying on the file's order
def load_credential(key: str) -> dict:
    """Return the {user, password} record stored under `key` in the credentials file."""
    users = _read_credentials()
    if key not in users:
        available = ", ".join(sorted(users)) or "(none)"
        raise KeyError(
            f"User '{key}' was not found in {CREDENTIALS_FILE}. Available: {available}."
        )
    return users[key]


# return the user keys (default, editor, ...) in the same order as load_credentials().
# use these as pytest `ids=` so each case is labelled by its key instead of an index.
# @parametrize runs at import time, so a missing credentials file yields no cases
# instead of breaking collection for the whole suite
def load_credential_ids() -> list[str]:
    """Return the credential keys (default, editor, ...) for use as pytest ids."""
    return list(_read_credentials().keys()) if CREDENTIALS_FILE.exists() else []


# return just the login names, in the same order as load_credential_ids().
# tests parametrize over these: Allure records every test parameter, so the password
# must never be one (see load_passwords_by_user below)
def load_credential_users() -> list[str]:
    """Return the user login names in the same order as load_credential_ids()."""
    return [record["user"] for record in load_credentials()] if CREDENTIALS_FILE.exists() else []


# return a user -> password map. the password is looked up inside the test from a
# fixture instead of being passed as a parameter, which keeps it out of the report
def load_passwords_by_user() -> dict[str, str]:
    """Return a {user: password} map for looking up a password at run time."""
    return {record["user"]: record["password"] for record in load_credentials()}


# placeholder token in payload templates, e.g. "<email>" or "<user_id>".
# any run-time value can be injected by passing it as a keyword to load_api_payload().
_PLACEHOLDER = re.compile(r"<([^<>]+)>")


# private helper: walk a loaded JSON structure (dict/list/str) and replace every
# <token> with the matching value from `params`. two substitution modes:
#   - exact match ("<order_id>")        -> replaced with the raw value (type preserved:
#                                          int stays int, nested dict stays dict, ...)
#   - embedded  ("id-<order_id>-x")     -> the token is replaced with str(value)
# a <token> with no matching param raises a clear KeyError naming the file.
def _render_placeholders(value: Any, params: dict, source: str) -> Any:
    if isinstance(value, dict):
        return {key: _render_placeholders(val, params, source) for key, val in value.items()}
    if isinstance(value, list):
        return [_render_placeholders(item, params, source) for item in value]
    if isinstance(value, str):
        exact = _PLACEHOLDER.fullmatch(value)
        if exact:
            return _lookup(exact.group(1), params, source)
        return _PLACEHOLDER.sub(lambda m: str(_lookup(m.group(1), params, source)), value)
    return value


# private helper: resolve one placeholder name against the provided params
def _lookup(token: str, params: dict, source: str) -> Any:
    if token not in params:
        available = ", ".join(sorted(params)) or "(none)"
        raise KeyError(
            f"Payload '{source}' needs placeholder <{token}>, "
            f"but it was not provided. Available: {available}."
        )
    return params[token]


# return an API request payload from data/api_payloads/<name>.json.
# any <placeholder> tokens in the file are replaced with the matching keyword
# arguments, e.g. load_api_payload("login", email=email, password=password).
def load_api_payload(name: str, **params: Any) -> dict:
    """Return an API request payload from data/api_payloads/<name>.json.

    Pass keyword arguments to substitute <placeholder> tokens in the file, e.g.
    load_api_payload("create_user", user_id="123") replaces "<user_id>".
    """
    payload = _read_json(DATA_DIR / "api_payloads" / f"{name}.json")
    return _render_placeholders(payload, params, name)


# return an expected-result definition from data/expected_results/<name>.json
def load_expected_result(name: str) -> dict:
    """Return an expected-result definition from data/expected_results/<name>.json."""
    return _read_json(DATA_DIR / "expected_results" / f"{name}.json")
