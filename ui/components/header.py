from ui.components.navigation_menu import NavigationMenu


# reusable header component shared by authenticated pages; exposes the nav menu.
# pages use composition (has-a Header) instead of deep inheritance
class Header:
    """Site header shared across authenticated pages; exposes the navigation menu."""

    # build the header and its nested navigation menu from the given page
    def __init__(self, page):
        self.page = page
        self.navigation = NavigationMenu(page)
