import allure

from ui.elements.base_element import BaseElement


# reusable button wrapper: adds a named Allure step around the click
class Button(BaseElement):
    # click the button and record it as a technical step in the report
    def click(self):
        with allure.step(f"Click '{self.name}'"):
            self.locator.click()
