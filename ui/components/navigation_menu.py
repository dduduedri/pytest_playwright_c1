import allure

from ui.elements.button import Button


# reusable UI area (component) for the top navigation shown after login.
# components group elements/actions that several pages can share
class NavigationMenu:
    """Top navigation actions available after login."""

    # build the navigation's elements from the given page
    def __init__(self, page):
        self.page = page
        self.orders_button = Button(page.get_by_role("button", name="ORDERS"), "ORDERS")

    # business action: go to the ORDERS section
    def open_orders(self):
        with allure.step("Navigate to ORDERS"):
            self.orders_button.click()
