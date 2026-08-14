import allure
from playwright.sync_api import Page, expect

from ui.elements.button import Button
from ui.elements.link import Link
from ui.pages.business_requests_page import BusinessRequestsPage


# the application shell's navigation menu: available on every page once logged in
class HamburgerMenu:

    def __init__(self, page: Page):
        self.page = page
        self.menu_button = Button(page.get_by_test_id("hamburger-menu"), "hamburger menu")
        self.business_requests_link = Link(
            page.get_by_test_id("businessRequests").get_by_text("Business Requests"),
            "Business Requests",
        )

    # business action: navigate to the Business Requests list
    @allure.step("UI · open the Business Requests menu")
    def open_business_requests(self) -> BusinessRequestsPage:
        self.menu_button.click()
        self.business_requests_link.click()
        return BusinessRequestsPage(self.page)

    # verification method: the menu only renders for an authenticated user, so it is
    # also the signal that the login redirect finished and the app shell is up
    @allure.step("UI · verify the application shell is loaded")
    def verify_available(self, timeout: float = None) -> None:
        expect(self.menu_button.locator).to_be_visible(timeout=timeout)
