from allianceauth.services.hooks import get_extension_logger
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ... import __title__
from ...utils import LoggerAddTag
from ...constants import EVE_CATEGORY_ID_MATERIAL, EVE_CATEGORY_ID_SHIP
from ...constants import EVE_CATEGORY_ID_MODULE, EVE_CATEGORY_ID_CHARGE
from ...constants import EVE_CATEGORY_ID_COMMODITY, EVE_CATEGORY_ID_DRONE
from ...constants import EVE_CATEGORY_ID_ASTEROID, EVE_CATEGORY_ID_FIGHTER
from ...constants import EVE_CATEGORY_ID_PLANETRAY_COMMODITY

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class Command(BaseCommand):
    help = "Preloads data required for aa-buybacks from ESI"

    def handle(self, *args, **options):
        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_MATERIAL),
        )

        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_SHIP),
        )

        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_MODULE),
        )

        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_CHARGE),
        )

        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_COMMODITY),
        )

        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_DRONE),
        )

        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_ASTEROID),
        )

        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_PLANETRAY_COMMODITY),
        )

        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_FIGHTER),
        )
