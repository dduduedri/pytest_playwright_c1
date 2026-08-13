import allure

from ui.elements.base_element import BaseElement


# reusable checkbox wrapper: adds named Allure steps around check/uncheck
class Checkbox(BaseElement):
    # tick the checkbox (no-op if already checked, thanks to Playwright)
    def check(self):
        with allure.step(f"Check '{self.name}'"):
            self.locator.check()

    # untick the checkbox
    def uncheck(self):
        with allure.step(f"Uncheck '{self.name}'"):
            self.locator.uncheck()

    # return True if the checkbox is currently ticked
    def is_checked(self) -> bool:
        return self.locator.is_checked()
