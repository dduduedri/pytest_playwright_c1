import allure
from playwright.sync_api import expect

from ui.elements.button import Button
from ui.elements.text_box import TextBox
from ui.pages.base_page import BasePage
from utils.data_reader import load_expected_result


# EXAMPLE page object - the reference for every page you add to this template.
# Point the three locators below at your application's login form; the structure
# (elements in __init__, business actions, verification method) stays the same.
#
# inherit from BasePage to share the `page` with all other page classes
class LoginPage(BasePage):

    # build the page and its elements once; locators are defined here (in the page),
    # wrapped as reusable elements that add Allure reporting
    def __init__(self, page):
        super().__init__(page)
        self.user = TextBox(page.get_by_label("Username or email"), "Username or email")
        self.password = TextBox(page.get_by_label("Password"), "Password")
        self.login_button = Button(page.get_by_role("button", name="Login"), "Login")

    # low-level action: fill the credentials and submit the form
    def login(self, user, password):
        self.user.fill(user)
        self.password.fill(password, mask=True)
        self.login_button.click()

    # business action: log in and hand back the page the app lands on.
    # inline step (not @allure.step) so the password argument is not
    # captured as a report parameter.
    # once you add the landing page object, return it here so tests can chain
    # page objects: `return DashboardPage(self.page)`
    def login_and_continue(self, user, password) -> None:
        with allure.step(f"UI · login (user: {user})"):
            self.login(user, password)

    # verification method: read the expected value from data/expected_results and
    # assert it. a page method may assert when it is explicitly a verification step
    @allure.step("UI · verify the user is logged in")
    def verify_logged_in(self) -> None:
        expected_heading = load_expected_result("login")["logged_in_heading"]
        with allure.step(f"Assert heading is visible · expected='{expected_heading}'"):
            expect(self.page.get_by_role("heading", name=expected_heading)).to_be_visible()
