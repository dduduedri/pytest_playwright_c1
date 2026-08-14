from datetime import date

import allure
from playwright.sync_api import Page, expect

from ui.elements.button import Button
from ui.elements.date_picker import DatePicker
from ui.elements.listbox_dropdown import ListboxDropdown
from ui.elements.text_box import TextBox
from ui.pages.business_request_details_page import BusinessRequestDetailsPage


# the "Create Business Request" modal, opened from the Business Requests list page
class CreateBrDialog:

    def __init__(self, page: Page):
        self.page = page
        # the name field is the modal's own marker: while it exists, the modal is open
        self.container = page.get_by_test_id("create-br-name")
        self.name = TextBox(self.container.get_by_test_id("text-control"), "Business Request name")
        self.due_date = DatePicker(
            page.get_by_test_id("create-br-due-date"),
            "Due date",
            apply_button=page.get_by_text("Apply", exact=True).first,
        )
        self.approval_flow = ListboxDropdown(
            page.get_by_test_id("create-br-approval-flow").locator("div").first,
            "Approval flow",
            options=page.get_by_role("listbox"),
        )
        # the control mirrors the committed selection into this attribute
        self.selected_approval_flow = page.get_by_test_id("create-br-approval-flow").locator(
            "div.truncate[data-test-text]"
        )
        self.create_and_open_button = Button(
            page.get_by_text("Create & Open").first, "Create & Open"
        )

    # business action: name the business request
    @allure.step("UI · fill the business request name")
    def fill_name(self, name: str) -> None:
        self.name.fill(name)

    # business action: set the due date through the calendar popup
    @allure.step("UI · set the due date")
    def set_due_date(self, day: date) -> None:
        self.due_date.select_date(day)

    # business action: choose the approval flow, then assert the control committed it -
    # the form silently resets the selection if it is submitted too early
    @allure.step("UI · select the approval flow")
    def select_approval_flow(self, flow: str) -> None:
        self.approval_flow.select(flow)
        with allure.step(f"Assert the selected approval flow · expected='{flow}'"):
            expect(self.selected_approval_flow).to_have_attribute("data-test-text", flow)

    # business action: submit the dialog and hand back the page the app opens
    @allure.step("UI · create the business request and open it")
    def create_and_open(self) -> BusinessRequestDetailsPage:
        self.create_and_open_button.click()
        # the dialog closes only after the app accepted the form, so a dialog that
        # stays open means the creation itself failed
        self.container.wait_for(state="hidden")
        return BusinessRequestDetailsPage(self.page)
