import allure
from playwright.sync_api import Locator

from ui.elements.base_element import BaseElement


# reusable wrapper for custom (non-<select>) dropdowns: clicking the control opens a
# listbox popup that the app renders outside the control, so the popup locator is
# passed in by the page object. use Dropdown instead for a native <select>.
class ListboxDropdown(BaseElement):
    # `options` is the open popup (usually page.get_by_role("listbox"))
    def __init__(self, locator: Locator, name: str, options: Locator):
        super().__init__(locator, name)
        self.options = options

    # open the control and pick the option by its visible label
    def select(self, option: str):
        with allure.step(f"Select '{option}' in '{self.name}'"):
            self.locator.click()
            self.options.get_by_text(option, exact=True).click()
