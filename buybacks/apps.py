from django.apps import AppConfig

from . import __version__


class BuybacksConfig(AppConfig):
    name = "buybacks"
    label = "buybacks"
    verbose_name = f"Buybacks v{__version__}"
