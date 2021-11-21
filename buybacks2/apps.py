from django.apps import AppConfig

from . import __version__


class BuybacksConfig(AppConfig):
    name = "buybacks2"
    label = "buybacks2"
    verbose_name = f"AA - Buybacks2 v{__version__}"
