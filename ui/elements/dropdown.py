import allure

from ui.elements.base_element import BaseElement


# reusable <select> dropdown wrapper: adds named Allure steps around selection
class Dropdown(BaseElement):
    # choose an option by its underlying value attribute
    def select_by_value(self, value: str):
        with allure.step(f"Select '{value}' in '{self.name}'"):
            self.locator.select_option(value=value)

    # choose an option by its visible label text
    def select_by_label(self, label: str):
        with allure.step(f"Select '{label}' in '{self.name}'"):
            self.locator.select_option(label=label)
