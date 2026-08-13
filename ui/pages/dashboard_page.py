import allure

from ui.components.header import Header
from ui.pages.base_page import BasePage
from ui.pages.order_history_page import OrderHistoryPage


# the page shown after login; composes the shared Header component
class DashboardPage(BasePage):

    # keep the page reference (via BasePage) and attach the reusable Header
    def __init__(self, page):
        super().__init__(page)
        self.header = Header(page)

    # business action: open the ORDERS area and return the next page object
    @allure.step("UI · open order history from dashboard")
    def order_nav_link_to_history(self) -> OrderHistoryPage:
        self.header.navigation.open_orders()
        return OrderHistoryPage(self.page)
