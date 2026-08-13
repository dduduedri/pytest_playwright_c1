import os
from pathlib import PurePath
from urllib.parse import quote

import allure

from utils.logger import get_logger

# module logger; streams live to the console via log_cli (see pytest.ini)
log = get_logger(__name__)

# root of every generated artifact; trace URLs are built relative to it
RESULTS_ROOT = "reports-results"

# set this to the URL where CI publishes the reports-results/ folder, e.g.
#   TRACE_BASE_URL=https://ci.example.com/job/e2e/42/artifact/reports-results
# when it is set, a failing test gets a one-click link that opens its trace in the
# Playwright viewer; when it is not (a normal local run) the report shows the command
# to open the trace instead, because the viewer has to fetch the zip over http(s)
TRACE_BASE_URL_ENV = "TRACE_BASE_URL"
TRACE_VIEWER_URL = "https://trace.playwright.dev/?trace="


# did the setup or call phase of this test fail? reads the phase reports stored on the
# test item by the pytest_runtest_makereport hook in conftest.py
def is_test_failed(node) -> bool:
    """True when this test's setup or call phase failed."""
    return bool(
        (getattr(node, "rep_setup", None) and node.rep_setup.failed)
        or (getattr(node, "rep_call", None) and node.rep_call.failed)
    )


# attach the readable failure trace, at most once per test.
# UI/e2e tests reach this from the browser context teardown and API-only tests from the
# request context teardown, so every layer produces the same evidence; the guard keeps
# a test that has both fixtures from attaching it twice
def attach_failure_traceback(node) -> None:
    """Attach the failure traceback for `node` to Allure, once per test."""
    if getattr(node, "_traceback_attached", False):
        return

    # prefer the pretty (Java-style) trace built in the makereport hook,
    # fall back to pytest's raw longrepr
    traceback_text = getattr(node, "_pretty_trace", None)
    if not traceback_text:
        traceback_text = "\n\n".join(
            report.longreprtext
            for report in (getattr(node, "rep_setup", None), getattr(node, "rep_call", None))
            if report is not None and report.failed and report.longreprtext
        )
    if not traceback_text:
        log.warning("[%s] no traceback available to attach", node.name)
        return

    # the step groups the attachment in the Tear down section; it lives here (after the
    # guard) so neither fixture can produce an empty group
    with allure.step("Automation trace code"):
        allure.attach(
            traceback_text,
            name="traceback · failure trace",
            attachment_type=allure.attachment_type.TEXT,
        )
    node._traceback_attached = True


# make the attached trace.zip actionable. Allure has no viewer for a zip, so the
# attachment itself can only be downloaded; this adds the way to actually open it
def attach_trace_pointer(trace_path: str) -> None:
    """Attach a one-click trace-viewer link, or the local command to open the trace."""
    base_url = os.environ.get(TRACE_BASE_URL_ENV, "").strip().rstrip("/")

    # local run: there is no URL the viewer could fetch, so hand over both manual ways
    # to open the downloaded trace. (the command is quoted because the test name
    # contains [] characters)
    if not base_url:
        allure.attach(
            "Option 1 — local viewer (CLI):\n"
            f'    playwright show-trace "{trace_path}"\n'
            "\n"
            "Option 2 — online viewer:\n"
            "    1. open https://trace.playwright.dev/\n"
            "    2. drag-and-drop this file onto the page:\n"
            f"       {trace_path}\n"
            "    the file is processed in your browser and is not uploaded anywhere.",
            name="trace · how to open",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    # published run: link straight into the viewer with the trace pre-loaded
    relative = PurePath(os.path.relpath(trace_path, RESULTS_ROOT)).as_posix()
    viewer_url = f"{TRACE_VIEWER_URL}{base_url}/{quote(relative)}"

    # the Links block at the top of the test (a no-op if the test is already closed)
    allure.dynamic.link(viewer_url, name="Open Playwright trace")
    # ...and as an attachment too, which Allure renders as a clickable link
    allure.attach(
        viewer_url,
        name="trace · open in viewer",
        attachment_type=allure.attachment_type.URI_LIST,
    )
