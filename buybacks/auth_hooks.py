from django.utils.translation import ugettext_lazy as _

from allianceauth.services.hooks import MenuItemHook, UrlHook
from allianceauth import hooks

from . import urls


class BuybacksMenuItem(MenuItemHook):
    """ This class ensures only authorized users will see the menu entry """

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _("Buybacks"),
            "fas fa-money-bill-wave fa-fw",
            "buybacks:index",
            navactive=["buybacks:"],
        )

    def render(self, request):
        if request.user.has_perm("buybacks.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    return BuybacksMenuItem()


@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "buybacks", r"^buybacks/")
