from playwright.sync_api import Locator


# parent class for reusable UI element wrappers (Button, TextBox, ...).
# it pairs a Playwright Locator with a human-readable name used in Allure steps
class BaseElement:
    """Reusable OOP wrapper around a Playwright Locator.

    Subclasses (Button, TextBox, ...) expose intent-revealing actions that
    emit Allure substeps using the human-readable `name`.
    """

    # store the locator (how to find the element) and its friendly name
    def __init__(self, locator: Locator, name: str):
        self.locator = locator
        self.name = name

    # wait until the element becomes visible on the page
    def wait_visible(self, timeout: float = None):
        self.locator.wait_for(state="visible", timeout=timeout)

    # return True if the element is currently visible
    def is_visible(self) -> bool:
        return self.locator.is_visible()
