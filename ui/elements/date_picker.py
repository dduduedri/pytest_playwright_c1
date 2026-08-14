from datetime import date

import allure
from playwright.sync_api import Locator

from ui.elements.base_element import BaseElement


# the calendar labels every day cell with its full date, e.g.
# "Choose Thursday, August 13th, 2026" - that label is how a day is picked
def choose_day_label(day: date) -> str:
    """Return the accessible label of a day cell, e.g. 'Choose Thursday, August 13th, 2026'."""
    if 11 <= day.day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day.day % 10, "th")
    return f"Choose {day:%A}, {day:%B} {day.day}{suffix}, {day.year}"


# reusable date-field wrapper: `locator` is the field, and because the calendar popup
# is rendered outside it, the page object passes the popup's Apply button in
class DatePicker(BaseElement):
    def __init__(self, locator: Locator, name: str, apply_button: Locator):
        super().__init__(locator, name)
        self.apply_button = apply_button

    # open the calendar by clicking the field's calendar icon
    def open(self):
        with allure.step(f"Open the '{self.name}' calendar"):
            self.locator.get_by_role("img").click()

    # confirm the current calendar selection
    def apply(self):
        with allure.step(f"Apply the '{self.name}' selection"):
            self.apply_button.click()

    # click one day cell in the open calendar
    def choose_day(self, day: date):
        with allure.step(f"Choose {day.isoformat()} in '{self.name}'"):
            self.locator.page.get_by_role("option", name=choose_day_label(day)).click()

    # set the field to `day`: the widget needs the first Apply to switch the popup
    # from its range/preset view to the day grid, and the second one to commit
    def select_date(self, day: date):
        with allure.step(f"Set '{self.name}' = {day.isoformat()}"):
            self.open()
            self.apply()
            self.choose_day(day)
            self.apply()
