import json
import linecache
import os
import shutil
import traceback
from pathlib import Path

import pytest

from utils.config_reader import ExecutionConfig
from utils.logger import get_logger

# module logger; streams live to the console via log_cli (see pytest.ini)
log = get_logger("conftest")

# fixtures live in dedicated modules and are registered as plugins
pytest_plugins = (
    "fixtures.ui_fixtures",
    "fixtures.api_fixtures",
    "fixtures.data_fixtures",
)

# pytest hook: register our custom CLI options. they all default to None and fall back
# to the config files at use time, so the run's --env decides before anything is read.
# --env/--browser_name/--url are custom; --tracing/--video/--headed come from pytest-playwright.
def pytest_addoption(parser):
    parser.addoption(
        "--env", action="store", default=None,
        help="environment to run against: a key of config/environment.json "
             "(default: \"environment\" in config/execution.json)",
    )
    parser.addoption(
        "--browser_name", action="store", default=None,
        help="playwright browser type: chromium | firefox | webkit",
    )
    parser.addoption(
        "--url", action="store", default=None,
        help="application url (default: the chosen environment's ui)",
    )
    # headed/headless override for this run. `--headed` is already provided by
    # pytest-playwright; we add `--headless` so either flag can override
    # config/execution.json's "headless" value (see browser_setup).
    parser.addoption(
        "--headless", action="store_true", default=False,
        help="force headless for this run (overrides config/execution.json)",
    )


# our fixtures write traces/videos here; allure's --clean-alluredir only clears
# allure-results, so we clean these ourselves to match that behavior
_RESULTS_ROOT = Path("reports-results")
_CLEAN_DIRS = ("test-results", "videos")


# pytest hook that runs once at startup:
#   1. resolve the run's settings for the chosen environment, so an unknown --env fails
#      here with a usage error instead of breaking the setup of every single test
#   2. when the user asks to clean allure results (--clean-alluredir), also wipe our
#      trace/video folders so old runs don't pile up
def pytest_configure(config):
    try:
        config.execution_config = ExecutionConfig.load(config.getoption("--env"))
    except (KeyError, FileNotFoundError, ValueError) as error:
        # args[0] is our own message; UsageError prints it without a traceback
        raise pytest.UsageError(error.args[0]) from None
    log.info("environment: %s", config.execution_config.environment_name)

    # skip on xdist workers (they have `workerinput`); only the controller cleans,
    # before workers start writing, so we don't delete freshly created results
    if hasattr(config, "workerinput"):
        return
    if not config.getoption("--clean-alluredir", default=False):
        return
    for name in _CLEAN_DIRS:
        target = _RESULTS_ROOT / name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            log.info("cleaned results folder: %s", target)


# Allure marks a setup/teardown entry with one of these when it actually completed.
# fixture finalizers that Allure only "starts" (e.g. plugin `::<lambda>` teardowns)
# have no status and render as noisy "Unknown" rows in the Teardown section.
_VALID_ALLURE_STATUSES = {"passed", "failed", "broken", "skipped"}


# remove the statusless ("Unknown") befores/afters from a single Allure container file
def _strip_unknown_fixture_steps(container_path: Path) -> None:
    try:
        data = json.loads(container_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return

    changed = False
    for section in ("befores", "afters"):
        entries = data.get(section)
        if not entries:
            continue
        kept = [e for e in entries if e.get("status") in _VALID_ALLURE_STATUSES]
        if len(kept) != len(entries):
            data[section] = kept
            changed = True

    if changed:
        container_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


# pytest hook that runs once after the whole session: clean the "Unknown" fixture
# rows out of the Allure teardown/setup view. trylast so Allure has finished writing.
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    config = session.config
    # only the xdist controller post-processes, after all workers have flushed results
    if hasattr(config, "workerinput"):
        return
    alluredir = config.getoption("--alluredir", default=None)
    if not alluredir:
        return
    for container_path in Path(alluredir).glob("*-container.json"):
        _strip_unknown_fixture_steps(container_path)


# session fixture: expose the run's settings (resolved in pytest_configure for the
# environment chosen with --env) to tests and other fixtures
@pytest.fixture(scope="session")
def execution_config(request) -> ExecutionConfig:
    return request.config.execution_config


# helper: build a readable, Java-style failure trace (used for the Allure attachment)
def _format_pretty_trace(excinfo, max_lines_per_frame=40):
    """Render a failure like the Java-style example: per-frame file header,
    numbered source lines, and a '==>' arrow on the active line.

    Only project frames (under the workspace) are shown, so third-party/internal
    frames don't clutter the trace.
    """
    workspace = os.path.normcase(os.getcwd())
    blocks = []

    for frame, lineno in traceback.walk_tb(excinfo.tb):
        filename = frame.f_code.co_filename
        if filename.startswith("<"):  # synthetic frames (e.g. <string>) have no source
            continue
        abspath = os.path.normcase(os.path.abspath(filename))

        # keep only the user's own code: under the workspace, but not the
        # virtualenv/installed packages, and not frames the libs mark as hidden
        if not abspath.startswith(workspace):
            continue
        if "site-packages" in abspath or f"{os.sep}.venv{os.sep}" in abspath:
            continue
        if frame.f_locals.get("__tracebackhide__"):
            continue

        # show from the enclosing function's def line down to the active line,
        # capped so very long functions don't explode the output
        start = frame.f_code.co_firstlineno
        if lineno - start > max_lines_per_frame:
            start = lineno - max_lines_per_frame

        rel_path = os.path.relpath(filename, os.getcwd())
        lines = [rel_path]
        for number in range(start, lineno + 1):
            source = linecache.getline(filename, number).rstrip("\n")
            marker = "==>" if number == lineno else "   "
            lines.append(f"{number:>4}: {marker} {source}")
        blocks.append("\n".join(lines))

    trace = "\n\n".join(blocks)
    error = f"{excinfo.type.__name__}: {excinfo.value}"
    return f"{trace}\n\n{error}" if trace else error


# pytest hook that runs for each test phase (setup/call/teardown): it records the
# result on the test item so fixtures can later tell if the test passed or failed
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)

    # build the pretty (Java-style) trace while the live exception info is available
    if report.failed and call.excinfo is not None:
        try:
            item._pretty_trace = _format_pretty_trace(call.excinfo)
        except Exception as error:
            log.warning("failed to build pretty trace: %s", error)
