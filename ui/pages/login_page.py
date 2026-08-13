import allure

from ui.elements.button import Button
from ui.elements.text_box import TextBox
from ui.pages.base_page import BasePage
from ui.pages.dashboard_page import DashboardPage


# inherit from BasePage to share the `page` with all other page classes
class LoginPage(BasePage):

    # build the page and its elements once; locators are defined here (in the page),
    # wrapped as reusable elements that add Allure reporting
    def __init__(self, page):
        super().__init__(page)
        self.email = TextBox(page.locator("#userEmail"), "Email")
        self.password = TextBox(page.locator("#userPassword"), "Password")
        self.login_button = Button(page.locator("#login"), "Login")

    # low-level action: fill the credentials and submit the form
    def login(self, user_email, user_password):
        self.email.fill(user_email)
        self.password.fill(user_password, mask=True)
        self.login_button.click()

    # business action: log in and hand back the next page (dashboard).
    # inline step (not @allure.step) so the password argument is not
    # captured as a report parameter
    def login_and_dashboard(self, user_email, user_password) -> DashboardPage:
        with allure.step("UI · login and open dashboard"):
            self.login(user_email, user_password)
            return DashboardPage(self.page)
