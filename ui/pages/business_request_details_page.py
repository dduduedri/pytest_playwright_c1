import re

import allure
from playwright.sync_api import Page, expect

from ui.pages.base_page import BasePage

# opening a business request lands on the designer, with the request's id in the query
BR_DETAILS_URL = re.compile(r"/designerLayout\?businessRequestId=[^&]+")

# creating the business request is a server-side operation before the details page
# renders; the legacy framework allowed 15 s for the Details menu to appear
DETAILS_TIMEOUT_MS = 15_000


# the details page of a single business request
class BusinessRequestDetailsPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.details_menu = page.locator("div.layout-menu-toggle div:text('Details')")

    # verification method: the app navigated to a business request and its page is loaded
    @allure.step("UI · verify the business request details page is open")
    def verify_opened(self) -> None:
        with allure.step(f"Assert the URL points at a business request · pattern='{BR_DETAILS_URL.pattern}'"):
            self.page.wait_for_url(BR_DETAILS_URL)
        with allure.step("Assert the Details menu is visible"):
            expect(self.details_menu).to_be_visible(timeout=DETAILS_TIMEOUT_MS)
