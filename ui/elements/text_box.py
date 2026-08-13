import allure

from ui.elements.base_element import BaseElement


# reusable text-input wrapper: adds Allure steps and can mask secret values
class TextBox(BaseElement):
    # replace the field content; mask=True hides secrets (e.g. passwords) in the report
    def fill(self, value: str, mask: bool = False):
        shown = "***" if mask else value
        with allure.step(f"Fill '{self.name}' = '{shown}'"):
            self.locator.fill(value)

    # type character by character (use when the app reacts to each keystroke)
    def type(self, value: str, mask: bool = False):
        shown = "***" if mask else value
        with allure.step(f"Type into '{self.name}' = '{shown}'"):
            self.locator.type(value)
