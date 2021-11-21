from bravado.exception import HTTPForbidden, HTTPUnauthorized

from django.db import models

from allianceauth.services.hooks import get_extension_logger
from esi.models import Token
from eveuniverse.models import EveSolarSystem

from .helpers import esi_fetch

logger = get_extension_logger(__name__)


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

        if location_id >= self.STATION_ID_START and location_id <= self.STATION_ID_END:
            logger.info("Fetching station from ESI")
            try:
                station = esi_fetch(
                    "Universe.get_universe_stations_station_id",
                    args={"station_id": location_id},
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
                logger.exception(f"Failed to load station: {ex}")
                raise ex
        else:
            try:
                structure = esi_fetch(
                    "Universe.get_universe_structures_structure_id",
                    args={"structure_id": location_id},
                    token=token,
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
                logger.warning(f"No access to this structure: {ex}")
                if add_unknown:
                    location, created = self.get_or_create(
                        id=location_id,
                        defaults={
                            "name": f"Unknown structure {location_id}",
                            "category_id": Location.CATEGORY_STRUCTURE_ID,
                        },
                    )
                else:
                    raise ex
            except Exception as ex:
                logger.exception(f"Failed to load structure: {ex}")
                raise ex

        return location, created
