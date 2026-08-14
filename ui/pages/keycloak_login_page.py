import allure
from playwright.sync_api import Page

from ui.elements.button import Button
from ui.elements.text_box import TextBox
from ui.pages.base_page import BasePage


# the identity provider's sign-in form the application redirects to when a session
# is missing. it authenticates the user; the application's own pages start after it
class KeycloakLoginPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.username = TextBox(page.locator("input[name='username'], #username").first, "Username or email")
        self.password = TextBox(page.locator("input[name='password']"), "Password")
        self.sign_in_button = Button(page.get_by_role("button", name="Sign In"), "Sign In")

    # business action: submit the credentials.
    # inline step (not @allure.step) so the password argument is not captured as a
    # report parameter
    def sign_in(self, username: str, password: str) -> None:
        with allure.step(f"UI · sign in (user: {username})"):
            self.username.fill(username)
            self.password.fill(password, mask=True)
            self.sign_in_button.click()
