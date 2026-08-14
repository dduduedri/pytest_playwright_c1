import allure
from playwright.sync_api import Page

from ui.components.create_br_dialog import CreateBrDialog
from ui.elements.button import Button
from ui.pages.base_page import BasePage


# the Business Requests list page
class BusinessRequestsPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.create_new_button = Button(page.get_by_text("Create New").first, "Create New")

    # business action: open the creation dialog and hand it to the caller
    @allure.step("UI · open the Create Business Request dialog")
    def click_create_new(self) -> CreateBrDialog:
        self.create_new_button.click()
        return CreateBrDialog(self.page)
