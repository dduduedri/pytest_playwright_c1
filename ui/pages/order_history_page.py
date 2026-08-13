import allure

from ui.pages.base_page import BasePage
from ui.pages.order_details_page import OrderDetailsPage


# the order-history table page; finds a specific order and opens its details
class OrderHistoryPage(BasePage):

    # locate the row that matches the given order id and click its "View" button
    def select_order_from_history(self, order_id):
        with allure.step(f"Locate order row · locator=//tbody/tr filter(has_text) · input order_id='{order_id}'"):
            order_raw = self.page.locator("//tbody/tr").filter(has_text=order_id)
        with allure.step("Click View · locator=//td/button[contains(text(), 'View')]"):
            order_raw.locator("//td/button[contains(text(), 'View')]").click()

    # business action: open the order and return the order-details page object
    @allure.step("UI · select order from history and open details")
    def select_order_from_history_and_details(self, order_id) -> OrderDetailsPage:
        self.select_order_from_history(order_id)
        return OrderDetailsPage(self.page)
