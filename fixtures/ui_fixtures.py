import os

import allure
import pytest
from playwright.sync_api import Browser, Playwright

from ui.components.hamburger_menu import HamburgerMenu
from ui.pages.keycloak_login_page import KeycloakLoginPage
from utils.config_reader import ExecutionConfig
from utils.logger import get_logger
from utils.report import attach_failure_traceback, attach_trace_pointer, is_test_failed

# module logger; streams live to the console via log_cli (see pytest.ini)
log = get_logger(__name__)


# session fixture: launch ONE browser for the whole run (fast); each test then
# opens its own fresh context/page below for isolation
@pytest.fixture(scope="session")
def browser_setup(playwright: Playwright, request, execution_config: ExecutionConfig):
    #get the arg from the command line : pytest -s --browser_name firefox
    # without the flag, config/execution.json decides
    browser_name = request.config.getoption("--browser_name") or execution_config.browser

    # teach page.get_by_test_id() which attribute the application under test uses
    # (config/execution.json: test_id_attribute)
    playwright.selectors.set_test_id_attribute(execution_config.test_id_attribute)

    # headless comes from config/execution.json by default, but a CLI flag wins:
    #   --headed   -> force headed (headless=False)   [provided by pytest-playwright]
    #   --headless -> force headless (headless=True)   [added in conftest.py]
    # if neither/both edge cases: --headed takes precedence, else fall back to config.
    headless = execution_config.headless
    if request.config.getoption("--headed", default=False):
        headless = False
    elif request.config.getoption("--headless", default=False):
        headless = True

    launch_kwargs = {"headless": headless}

    # `chromium` is the Playwright browser type; branded Google Chrome is selected via
    # the `channel` option (config.browser_channel), not by using "chrome" as the type.
    if browser_name in ("chromium", "chrome"):
        if execution_config.browser_channel:
            launch_kwargs["channel"] = execution_config.browser_channel
        # the context's ignore_https_errors covers what Playwright itself requests; an
        # environment whose certificate the machine does not trust needs the flag at
        # process level too, or Chromium refuses the page before it loads
        if execution_config.ignore_https_errors:
            launch_kwargs["args"] = ["--ignore-certificate-errors"]
        browser = playwright.chromium.launch(**launch_kwargs)
    elif browser_name == "firefox":
        browser = playwright.firefox.launch(**launch_kwargs)
    elif browser_name == "webkit":
        browser = playwright.webkit.launch(**launch_kwargs)
    else:
        browser = playwright.chromium.launch(**launch_kwargs)

    log.info(
        "browser launched: %s (headless=%s, channel=%s)",
        browser_name, headless, launch_kwargs.get("channel", "bundled"),
    )
    yield browser

    browser.close()
    log.info("browser closed")


# function fixture: give each test a fresh page in its own browser context.
# code before `yield` = setup; code after `yield` = teardown (tracing/video/failure artifacts)
@pytest.fixture(scope="function")
def context_setup(browser_setup: Browser, request, execution_config: ExecutionConfig):

    # read run options (from CLI or defaults) that control tracing and video
    trace_mode = request.config.getoption("--tracing")
    tracing_on = trace_mode in ("on", "retain-on-failure")
    video_mode = request.config.getoption("--video")
    record_video = video_mode in ("on", "retain-on-failure")

    context_kwargs = {"ignore_https_errors": execution_config.ignore_https_errors}
    if record_video:
        video_dir = os.path.join("reports-results", "videos", request.node.name)
        context_kwargs["record_video_dir"] = video_dir

    context = browser_setup.new_context(**context_kwargs)

    if tracing_on:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

    # open the tab
    page = context.new_page()

    # collect browser-side problems as they happen, so we can attach them on failure.
    # these lists fill up in the background via the event listeners registered below
    console_errors: list[str] = []
    network_errors: list[str] = []

    # browser console messages: keep only errors/warnings (msg.type is "error"/"warning"/...)
    def _on_console(message):
        if message.type in ("error", "warning"):
            console_errors.append(f"[{message.type}] {message.text}")

    # uncaught JavaScript exceptions thrown by the page
    def _on_page_error(exception):
        console_errors.append(f"[pageerror] {exception}")

    # requests that failed at the network level (DNS, connection reset, blocked, ...)
    def _on_request_failed(failed_request):
        network_errors.append(
            f"[requestfailed] {failed_request.method} {failed_request.url} :: {failed_request.failure}"
        )

    # responses that came back with an HTTP error status (4xx / 5xx)
    def _on_response(response):
        if response.status >= 400:
            network_errors.append(
                f"[HTTP {response.status}] {response.request.method} {response.url}"
            )

    page.on("console", _on_console)
    page.on("pageerror", _on_page_error)
    page.on("requestfailed", _on_request_failed)
    page.on("response", _on_response)

    # apply the default timeout, land on the app URL, then hand the page to the test.
    # --url overrides for this run; otherwise it is the chosen environment's ui
    page.set_default_timeout(execution_config.default_timeout_ms)
    target_url = request.config.getoption("--url") or execution_config.application_url
    log.info("[%s] navigating to %s", request.node.name, target_url)
    page.goto(url=target_url)
    yield page  # <-- the test runs here; everything below is teardown

    # did this test fail? (the makereport hook in conftest stored the phase results)
    test_failed = is_test_failed(request.node)

    # `--tracing on` keeps every trace; `retain-on-failure` keeps only the failures,
    # so stopping without a path discards the trace of a passing test
    if tracing_on:
        if trace_mode == "on" or test_failed:
            trace_path = os.path.join("reports-results", "test-results", request.node.name, "trace.zip")
            context.tracing.stop(path=trace_path)
            log.info("[%s] trace saved: %s", request.node.name, trace_path)
            # ship the trace with the failure, plus a pointer on how to open it
            # (Allure can only offer a zip for download, never render it)
            if test_failed:
                with allure.step("Playwright trace"):
                    allure.attach.file(
                        trace_path,
                        name="trace · playwright trace",
                        attachment_type=allure.attachment_type.ZIP,
                    )
                    attach_trace_pointer(trace_path)
        else:
            context.tracing.stop()
            log.info("[%s] trace discarded (test passed)", request.node.name)

    # the screenshot needs a live page but the video file only exists once the context
    # is closed, so grab the bytes now and attach both together further down
    screenshot_png = None
    if test_failed:
        log.warning("[%s] test failed - capturing failure artifacts", request.node.name)
        try:
            screenshot_png = page.screenshot(full_page=True)
        except Exception as error:
            log.error("[%s] failed to capture failure screenshot: %s", request.node.name, error)

    # capture the video target path before closing (the file is finalized on close)
    video_path = page.video.path() if record_video and page.video else None

    context.close()

    # the readable failure trace (shared with the API fixture, so an API-only test
    # gets the same evidence without a browser); it groups itself under a step
    if test_failed:
        attach_failure_traceback(request.node)

    # `on` keeps every recording; `retain-on-failure` keeps only the failures
    keep_video = bool(
        video_path
        and os.path.exists(video_path)
        and (video_mode == "on" or (video_mode == "retain-on-failure" and test_failed))
    )

    if screenshot_png or keep_video:
        with allure.step("UI screenshot/video"):
            if screenshot_png:
                allure.attach(
                    screenshot_png,
                    name="screenshot · failure state",
                    attachment_type=allure.attachment_type.PNG,
                )
            if keep_video:
                allure.attach.file(
                    video_path,
                    name="video · execution recording",
                    attachment_type=allure.attachment_type.WEBM,
                )
                log.info("[%s] video attached: %s", request.node.name, video_path)

    if video_path and not keep_video and os.path.exists(video_path):
        os.remove(video_path)
        log.info("[%s] video discarded (test passed)", request.node.name)

    # both logs are always attached on failure, so the section is present even when
    # nothing was captured (makes it clear the capture ran)
    if test_failed:
        with allure.step("Browser console/network"):
            allure.attach(
                "\n".join(console_errors) if console_errors else "No console errors/warnings captured during the test.",
                name="browser console errors",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                "\n".join(network_errors) if network_errors else "No network failures / HTTP error responses captured during the test.",
                name="browser network errors",
                attachment_type=allure.attachment_type.TEXT,
            )


# function fixture: a page with an authenticated session. the application redirects an
# anonymous visitor to the identity provider, so every UI test starts here instead of
# repeating the login itself
@pytest.fixture(scope="function")
def logged_in_page(context_setup, login_user: dict, execution_config: ExecutionConfig):
    page = context_setup
    KeycloakLoginPage(page).sign_in(login_user["user"], login_user["password"])
    # the navigation menu renders only for an authenticated user
    HamburgerMenu(page).verify_available(timeout=execution_config.default_timeout_ms)
    log.info("logged in as %s", login_user["user"])
    return page
