"""Reusable page sections shared by several pages (header, navigation, dialog,
data table, toast, date picker, ...).

Add a component when the same group of elements and actions appears on more than
one page, then compose it into the page objects that use it:

    class DashboardPage(BasePage):
        def __init__(self, page):
            super().__init__(page)
            self.header = Header(page)
"""
