import allure
from playwright.sync_api import expect

from ui.pages.base_page import BasePage
from utils.data_reader import load_expected_result


# the order-details page; holds the verification of the confirmation message
class OrderDetailsPage(BasePage):

    # verification method: read the expected text from data and assert the tagline.
    # (a page method is allowed to assert when it is explicitly a verification step)
    @allure.step("UI · verify order confirmation message")
    def verify_order_message(self):
        expected_text = load_expected_result("order_confirmation")["tagline"]
        with allure.step(f"Assert tagline · locator=//p[@class='tagline'] · expected='{expected_text}'"):
            expect(self.page.locator("//p[@class='tagline']")).to_have_text(expected_text)
