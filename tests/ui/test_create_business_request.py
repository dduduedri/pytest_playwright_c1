from datetime import date

import allure
import pytest

from ui.components.hamburger_menu import HamburgerMenu
from utils.test_data import unique_name

# the approval flow that lets a business request be created without an approver
NO_APPROVAL_REQUIRED = "No Approval Required"


@allure.epic("Catalog One")
@allure.feature("Business Request")
@allure.story("Create a business request")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("group21", "group80", "group98", "group99")
@allure.title("Create a business request that needs no approval")
@pytest.mark.ui
def test_create_business_request(logged_in_page):
    business_request_name = unique_name("br")

    business_requests_page = HamburgerMenu(logged_in_page).open_business_requests()
    create_dialog = business_requests_page.click_create_new()

    create_dialog.fill_name(business_request_name)
    create_dialog.set_due_date(date.today())
    create_dialog.select_approval_flow(NO_APPROVAL_REQUIRED)

    business_request = create_dialog.create_and_open()
    business_request.verify_opened()
