import json
from typing import Any

import allure
from playwright.sync_api import APIRequestContext, APIResponse

from utils.logger import get_logger

# module logger; streams live to the console via log_cli (see pytest.ini)
log = get_logger(__name__)

# any key containing one of these is replaced with *** before it is attached,
# so a request body can never carry a secret into the report
_SECRET_KEY_HINTS = ("password", "token", "authorization", "secret", "apikey", "api_key")

# error bodies can be huge (HTML error pages); attach only the useful head of one
_MAX_BODY_CHARS = 2000


# private helper: does this key name look like it holds a secret?
def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in _SECRET_KEY_HINTS)


# return a copy of a payload with every secret-looking value replaced by ***.
# nested dicts and lists are walked, so templates of any shape are covered
def mask_secrets(value: Any) -> Any:
    """Return a copy of `value` with secret-looking fields replaced by '***'."""
    if isinstance(value, dict):
        return {
            key: ("***" if _is_secret_key(key) else mask_secrets(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [mask_secrets(item) for item in value]
    return value


# helper: attach a Python object to the Allure report as pretty-printed JSON.
# masking happens here (the single choke point) so every caller is safe by default
def attach_json(name, payload):
    allure.attach(
        json.dumps(mask_secrets(payload), indent=2, ensure_ascii=False),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


# helper: attach any value to the Allure report as plain text
def attach_text(name, text):
    allure.attach(str(text), name=name, attachment_type=allure.attachment_type.TEXT)


# parent class for API clients: wraps Playwright's APIRequestContext and adds
# common headers + Allure steps. Domain clients (AuthApi, ...) inherit it.
class BaseApi:
    """Thin wrapper over Playwright's APIRequestContext with Allure attachments."""

    # keep the request context (the HTTP session with a base_url) for reuse
    def __init__(self, request_context: APIRequestContext):
        self.request_context = request_context

    # merge a default JSON content-type with any caller-provided headers
    def _default_headers(self, headers):
        merged = {"Content-Type": "application/json"}
        if headers:
            merged.update(headers)
        return merged

    # attach what the report needs about a response: always the status/url, plus the
    # body when the call failed (an API-only test has no screenshot to fall back on)
    def _attach_response(self, response: APIResponse) -> None:
        attach_text("response · meta", f"status: {response.status}\nurl: {response.url}")
        if response.status < 400:
            return
        try:
            body = response.text()
        except Exception as error:  # binary or already-consumed body
            log.warning("could not read error response body: %s", error)
            return
        if len(body) > _MAX_BODY_CHARS:
            body = f"{body[:_MAX_BODY_CHARS]}\n… truncated ({len(body)} characters total)"
        attach_text("response · error body", body)

    # send a POST request, record it as a step, and attach response metadata
    def post(self, endpoint, data=None, headers=None):
        with allure.step(f"POST {endpoint}"):
            response = self.request_context.post(
                endpoint, data=data, headers=self._default_headers(headers)
            )
            self._attach_response(response)
            log.info("POST %s -> %s", endpoint, response.status)
            return response

    # send a GET request, record it as a step, and attach response metadata
    def get(self, endpoint, headers=None):
        with allure.step(f"GET {endpoint}"):
            response = self.request_context.get(endpoint, headers=self._default_headers(headers))
            self._attach_response(response)
            log.info("GET %s -> %s", endpoint, response.status)
            return response

    # send a PUT request, record it as a step, and attach response metadata
    def put(self, endpoint, data=None, headers=None):
        with allure.step(f"PUT {endpoint}"):
            response = self.request_context.put(
                endpoint, data=data, headers=self._default_headers(headers)
            )
            self._attach_response(response)
            log.info("PUT %s -> %s", endpoint, response.status)
            return response

    # send a DELETE request, record it as a step, and attach response metadata
    def delete(self, endpoint, headers=None):
        with allure.step(f"DELETE {endpoint}"):
            response = self.request_context.delete(endpoint, headers=self._default_headers(headers))
            self._attach_response(response)
            log.info("DELETE %s -> %s", endpoint, response.status)
            return response
