from django.core.management import call_command
from django.core.management.base import BaseCommand

from ... import __title__
from ...constants import EVE_CATEGORY_ID_MATERIAL, EVE_CATEGORY_ID_SHIP
from ...constants import EVE_CATEGORY_ID_MODULE, EVE_CATEGORY_ID_CHARGE
from ...constants import EVE_CATEGORY_ID_COMMODITY, EVE_CATEGORY_ID_DRONE
from ...constants import EVE_CATEGORY_ID_ASTEROID, EVE_CATEGORY_ID_FIGHTER
from ...constants import EVE_CATEGORY_ID_PLANETRAY_COMMODITY
from ...constants import EVE_GROUP_ID_HARVESTABLE_CLOUD


class Command(BaseCommand):
    help = "Preloads data required for aa-buybacks from ESI"

    def handle(self, *args, **options):
        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_MATERIAL),
            "--category_id",
            str(EVE_CATEGORY_ID_SHIP),
            "--category_id",
            str(EVE_CATEGORY_ID_MODULE),
            "--category_id",
            str(EVE_CATEGORY_ID_CHARGE),
            "--category_id",
            str(EVE_CATEGORY_ID_COMMODITY),
            "--category_id",
            str(EVE_CATEGORY_ID_DRONE),
            "--category_id",
            str(EVE_CATEGORY_ID_ASTEROID),
            "--category_id",
            str(EVE_CATEGORY_ID_PLANETRAY_COMMODITY),
            "--category_id",
            str(EVE_CATEGORY_ID_FIGHTER),
            "--group_id",
            str(EVE_GROUP_ID_HARVESTABLE_CLOUD),
        )
