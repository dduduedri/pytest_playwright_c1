from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# resolve paths relative to the project root so the config is found from any cwd.
# the two files answer different questions:
#   environment.json -> WHERE the run points (one entry per environment)
#   execution.json   -> HOW the run behaves (browser, headless, timeout) and WHICH
#                       environment of environment.json to use
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
ENVIRONMENT_CONFIG = CONFIG_DIR / "environment.json"
EXECUTION_CONFIG = CONFIG_DIR / "execution.json"


# private helper: read a config file, naming it in the error if it is missing
def _read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file was not found: {path}")
    with path.open(encoding="utf-8") as config_file:
        return json.load(config_file)


# private helper: pick the environment to run against, naming in every error where the
# choice came from and which names are on offer
def _select_environment(
    environments: dict[str, Any], name: str | None, source: str
) -> tuple[str, dict]:
    available = ", ".join(environments) or "(none)"
    if not environments:
        raise KeyError(f"{ENVIRONMENT_CONFIG} defines no environment.")
    if name:
        if name not in environments:
            raise KeyError(
                f"Environment '{name}' ({source}) is not defined in {ENVIRONMENT_CONFIG}. "
                f"Available: {available}."
            )
        return name, environments[name]
    # a single environment leaves nothing to choose; several make the run ambiguous
    if len(environments) == 1:
        return next(iter(environments.items()))
    raise KeyError(
        f"{ENVIRONMENT_CONFIG} defines several environments, so the run is ambiguous. "
        f'Pass --env, or set "environment" in {EXECUTION_CONFIG}, to one of: {available}.'
    )


# typed, read-only holder for the settings of one run, merged from the two config files.
# frozen=True makes instances immutable (settings shouldn't change mid-run)
@dataclass(frozen=True) # dataclass - automatically creates __init__ no need to write self.attribute = attribute
class ExecutionConfig:
    environment_name: str
    application_url: str
    api_url: str
    keycloak_url: str | None
    asm_url: str | None
    pos_url: str | None
    browser: str
    browser_channel: str | None
    headless: bool
    default_timeout_ms: int
    test_id_attribute: str
    ignore_https_errors: bool

    # read both JSON config files and build one typed ExecutionConfig from them.
    # `environment_name` is the run's choice (pytest --env); without it the
    # "environment" key of execution.json decides
    @classmethod #classmethod - no need to create object to use the method
    def load(cls, environment_name: str | None = None) -> "ExecutionConfig":
        environments = _read_config(ENVIRONMENT_CONFIG)
        execution = _read_config(EXECUTION_CONFIG)

        if environment_name:
            name, environment = _select_environment(
                environments, environment_name, "passed with --env"
            )
        else:
            name, environment = _select_environment(
                environments, execution.get("environment"), f"set in {EXECUTION_CONFIG}"
            )

        # the UI and API hosts have no default: an unset one must fail loudly rather
        # than silently point the run at the wrong application
        for required_key in ("ui", "apiHost"):
            if not environment.get(required_key):
                raise KeyError(
                    f"'{required_key}' is missing from environment '{name}' in "
                    f"{ENVIRONMENT_CONFIG}. Set it to your application's URL."
                )

        # map the environment's service URLs and the run settings onto typed fields,
        # applying sensible defaults for the optional ones
        return cls(
            environment_name=name,
            application_url=environment["ui"],
            api_url=environment["apiHost"],
            # extra services: only the environments that expose them define these
            keycloak_url=environment.get("keycloakUrl"),
            asm_url=environment.get("a3sUrl"),
            pos_url=environment.get("posUrl"),
            browser=execution.get("browser", "chromium"),
            browser_channel=execution.get("browser_channel"),
            headless=execution.get("headless", True),
            default_timeout_ms=execution.get("default_timeout_ms", 30000),
            # the attribute page.get_by_test_id() looks at; "data-testid" is Playwright's
            # default, so set this only when the application marks elements differently
            test_id_attribute=execution.get("test_id_attribute", "data-testid"),
            # set this only for an environment served with a self-signed / internal
            # certificate, where the browser would otherwise refuse to open the app
            ignore_https_errors=execution.get("ignore_https_errors", False),
        )
