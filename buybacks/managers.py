from django.db import models
from allianceauth.services.hooks import get_extension_logger
from esi.models import Token
from bravado.exception import HTTPUnauthorized, HTTPForbidden
from eveuniverse.models import EveSolarSystem

from . import __title__
from .utils import LoggerAddTag, make_logger_prefix
from .helpers import esi_fetch


# Create your managers here.

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class LocationManager(models.Manager):
    STATION_ID_START = 60000000
    STATION_ID_END = 69999999

    def get_or_create_from_esi(
        self, token: Token, location_id: int, add_unknown: bool = True
    ) -> tuple:
        """gets or creates location object with data fetched from ESI"""
        from .models import Location

        try:
            location = self.get(id=location_id)
            created = False
        except Location.DoesNotExist:
            location, created = self.update_or_create_from_esi(
                token=token, location_id=location_id, add_unknown=add_unknown
            )

        return location, created

    def update_or_create_from_esi(
        self, token: Token, location_id: int, add_unknown: bool = True
    ) -> tuple:
        """updates or creates location object with data fetched from ESI"""
        from .models import Location

        add_prefix = make_logger_prefix(location_id)

        if location_id >= self.STATION_ID_START and location_id <= self.STATION_ID_END:
            logger.info(add_prefix("Fetching station from ESI"))
            try:
                station = esi_fetch(
                    "Universe.get_universe_stations_station_id",
                    args={"station_id": location_id},
                    logger_tag=add_prefix(),
                )

                eve_solar_system, _ = EveSolarSystem.objects.get_or_create_esi(
                    id=station["system_id"]
                )

                location, created = self.update_or_create(
                    id=location_id,
                    defaults={
                        "name": station["name"],
                        "eve_solar_system": eve_solar_system,
                        "category_id": Location.CATEGORY_STATION_ID,
                    },
                )
            except Exception as ex:
                logger.exception(add_prefix(
                    "Failed to load station: {}".format(ex)))
                raise ex
        else:
            try:
                structure = esi_fetch(
                    "Universe.get_universe_structures_structure_id",
                    args={"structure_id": location_id},
                    token=token,
                    logger_tag=add_prefix(),
                )

                eve_solar_system, _ = EveSolarSystem.objects.get_or_create_esi(
                    id=structure["solar_system_id"]
                )

                location, created = self.update_or_create(
                    id=location_id,
                    defaults={
                        "name": structure["name"],
                        "eve_solar_system": eve_solar_system,
                        "category_id": Location.CATEGORY_STRUCTURE_ID,
                    },
                )
            except (HTTPUnauthorized, HTTPForbidden) as ex:
                logger.warn(add_prefix(
                    "No access to this structure: {}".format(ex)))
                if add_unknown:
                    location, created = self.get_or_create(
                        id=location_id,
                        defaults={
                            "name": "Unknown structure {}".format(location_id),
                            "category_id": Location.CATEGORY_STRUCTURE_ID,
                        },
                    )
                else:
                    raise ex
            except Exception as ex:
                logger.exception(add_prefix(
                    "Failed to load structure: {}".format(ex)))
                raise ex

        return location, created
