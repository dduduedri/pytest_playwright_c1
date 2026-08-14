import allure

from ui.elements.base_element import BaseElement


# reusable link wrapper: adds a named Allure step around the navigation click
class Link(BaseElement):
    # follow the link and record it as a technical step in the report
    def click(self):
        with allure.step(f"Click link '{self.name}'"):
            self.locator.click()
