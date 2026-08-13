from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


# resolve paths relative to the project root so the config is found from any cwd
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXECUTION_CONFIG = PROJECT_ROOT / "config" / "execution.json"


# typed, read-only holder for execution settings loaded from config/execution.json.
# frozen=True makes instances immutable (settings shouldn't change mid-run)
@dataclass(frozen=True) # dataclass - automatically creates __init__ no need to write self.attribute = attribute
class ExecutionConfig:
    application_url: str
    api_url: str
    browser: str
    browser_channel: str | None
    headless: bool
    default_timeout_ms: int

    # read the JSON config file and build a typed ExecutionConfig from it
    @classmethod #classmethod - no need to create object to use the method
    def load(cls) -> "ExecutionConfig":
        # fail with a clear message if the config file is missing
        if not EXECUTION_CONFIG.exists():
            raise FileNotFoundError(
                f"Execution configuration was not found: {EXECUTION_CONFIG}"
            )

        with EXECUTION_CONFIG.open(encoding="utf-8") as config_file:
            data = json.load(config_file)

        # map JSON keys to fields, applying sensible defaults for optional ones
        return cls(
            application_url=data["application_url"],
            api_url=data.get("api_url", "https://rahulshettyacademy.com"),
            browser=data.get("browser", "chromium"),
            browser_channel=data.get("browser_channel"),
            headless=data.get("headless", True),
            default_timeout_ms=data.get("default_timeout_ms", 30000),
        )
