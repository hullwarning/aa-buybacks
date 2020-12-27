from typing import Tuple
from django.db import models
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenExpiredError, TokenInvalidError
from esi.models import Token
from eveuniverse.models import EveSolarSystem

from . import __title__
from .helpers import esi_fetch
from .utils import LoggerAddTag, make_logger_prefix
from .managers import LocationManager

# Create your models here.

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

OFFICE_TYPE_ID = 27


class Buybacks(models.Model):
    """Meta model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('basic_access', 'Can access this app'),
            ('setup_retriever', 'Can setup information retriever'),
            ('manage_programs', 'Can manage buyback programs'),
        )


class Corporation(models.Model):
    """A corporation that has buyback programs"""

    ERROR_NONE = 0
    ERROR_TOKEN_INVALID = 1
    ERROR_TOKEN_EXPIRED = 2
    ERROR_ESI_UNAVAILABLE = 5

    ERRORS_LIST = [
        (ERROR_NONE, "No error"),
        (ERROR_TOKEN_INVALID, "Invalid token"),
        (ERROR_TOKEN_EXPIRED, "Expired token"),
        (ERROR_ESI_UNAVAILABLE, "ESI API is currently unavailable"),
    ]

    corporation = models.OneToOneField(
        EveCorporationInfo,
        primary_key=True,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    character = models.ForeignKey(
        CharacterOwnership,
        on_delete=models.deletion.PROTECT,
        related_name="+",
    )

    class Meta:
        default_permissions = ()

    def update_offices_esi(self):
        token = self.token(
            [
                "esi-universe.read_structures.v1",
                "esi-assets.read_corporation_assets.v1",
            ]
        )[0]

        assets = esi_fetch(
            "Assets.get_corporations_corporation_id_assets",
            args={"corporation_id": self.corporation.corporation_id},
            has_pages=True,
            token=token,
            logger_tag=self._logger_prefix(),
        )

        office_ids_to_remove = list(
            Office.objects.filter(
                corporation=self).values_list("id", flat=True)
        )

        for asset in assets:
            if asset['type_id'] == OFFICE_TYPE_ID:
                location = Location.objects.get_or_create_from_esi(
                    location_id=asset['location_id'],
                    token=token,
                )[0]

                office_id = asset['item_id']
                office = Office.objects.filter(pk=office_id).first()

                if office is not None:
                    office_ids_to_remove.remove(office.id)
                else:
                    Office.objects.create(
                        id=office_id,
                        corporation=self,
                        location=location,
                    )

        Office.objects.filter(pk__in=office_ids_to_remove).delete()

    def token(self, scopes=None) -> Tuple[Token, int]:
        """returns a valid Token for the character"""
        token = None
        error = None
        add_prefix = self._logger_prefix()

        try:
            # get token
            token = (
                Token.objects.filter(
                    user=self.character.user,
                    character_id=self.character.character.character_id,
                )
                .require_scopes(scopes)
                .require_valid()
                .first()
            )
        except TokenInvalidError:
            logger.error(add_prefix("Invalid token for fetching information"))
            error = self.ERROR_TOKEN_INVALID
        except TokenExpiredError:
            logger.error(add_prefix("Token expired for fetching information"))
            error = self.ERROR_TOKEN_EXPIRED
        else:
            if not token:
                logger.error(add_prefix(
                    "No token found with sufficient scopes"))
                error = self.ERROR_TOKEN_INVALID

        return token, error

    def _logger_prefix(self):
        """returns standard logger prefix function"""
        return make_logger_prefix(self.corporation.corporation_ticker)

    def __str__(self):
        return self.corporation.corporation_name


class Location(models.Model):
    """An Eve Online buyback location: station or Upwell structure"""

    CATEGORY_UNKNOWN_ID = 0
    CATEGORY_STATION_ID = 3
    CATEGORY_STRUCTURE_ID = 65
    CATEGORY_CHOICES = [
        (CATEGORY_STATION_ID, "station"),
        (CATEGORY_STRUCTURE_ID, "structure"),
        (CATEGORY_UNKNOWN_ID, "(unknown)"),
    ]

    id = models.BigIntegerField(
        primary_key=True,
    )
    name = models.CharField(
        max_length=100,
        help_text="In-game name of this station or structure"
    )
    eve_solar_system = models.ForeignKey(
        EveSolarSystem,
        blank=True,
        default=None,
        null=True,
        on_delete=models.deletion.SET_DEFAULT,
        related_name="+",
    )
    category_id = models.PositiveIntegerField(
        choices=CATEGORY_CHOICES,
        default=CATEGORY_UNKNOWN_ID,
    )

    objects = LocationManager()

    def __str__(self):
        return self.name

    def __repr__(self) -> str:
        return "{}(pk={}, name='{}')".format(
            self.__class__.__name__, self.pk, self.name
        )

    @property
    def category(self):
        return self.category_id

    @property
    def solar_system_name(self):
        return self.name.split(" ", 1)[0]

    @property
    def location_name(self):
        return self.name.rsplit("-", 1)[1].strip()


class Office(models.Model):
    """An Eve Online buyback office for a corp: station or Upwell structure"""

    id = models.BigIntegerField(
        primary_key=True,
    )
    corporation = models.ForeignKey(
        Corporation,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
