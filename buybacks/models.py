import json
from typing import Tuple

from django.db import models
from django.contrib.auth.models import User
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenExpiredError, TokenInvalidError
from esi.models import Token
from eveuniverse.models import EveSolarSystem, EveType

from . import __title__
from .helpers import esi_fetch
from .utils import LoggerAddTag, make_logger_prefix
from .managers import LocationManager
from .validators import validate_brokerage

# Create your models here.

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

OFFICE_TYPE_ID = 27


class Buybacks(models.Model):
    """Meta model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("setup_retriever", "Can setup information retriever"),
            ("manage_programs", "Can manage buyback programs"),
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
        help_text="Character used for retrieving info",
        on_delete=models.deletion.PROTECT,
        related_name="+",
    )

    class Meta:
        default_permissions = ()

    def sync_contracts_esi(self):
        token = self.token(
            [
                "esi-contracts.read_corporation_contracts.v1",
            ]
        )[0]

        contracts = esi_fetch(
            "Contracts.get_corporations_corporation_id_contracts",
            args={
                "corporation_id": self.corporation.corporation_id,
            },
            has_pages=True,
            token=token,
        )

        buybacks = [
            x
            for x in contracts
            if x["type"] == "item_exchange"
            and x["status"] == "finished"
            and int(x["assignee_id"]) == self.corporation.corporation_id
        ]

        for contract in buybacks:
            notification = Notification.objects.filter(
                program_location__office__location__id=contract["start_location_id"],
                total=contract["price"],
                user__character_ownerships__character__character_id=contract[
                    "issuer_id"
                ],
            ).first()

            if notification is not None:
                items = esi_fetch(
                    "Contracts.get_corporations_corporation_id_contracts_contract_id_items",
                    args={
                        "corporation_id": self.corporation.corporation_id,
                        "contract_id": contract["contract_id"],
                    },
                    token=token,
                )

                quantities = {}

                for item in items:
                    if item["is_included"]:
                        type_id = int(item["type_id"])
                        quantity = int(item["quantity"])

                        if type_id in quantities:
                            quantities[type_id] += quantity
                        else:
                            quantities[type_id] = quantity

                data = json.loads(notification.items)
                match = True

                for type_id in data:
                    type_id = int(type_id)

                    if (
                        type_id not in quantities
                        or quantities[type_id] != data[str(type_id)]
                    ):
                        match = False

                if match:
                    character = CharacterOwnership.objects.filter(
                        character__character_id=contract["issuer_id"]
                    ).first()

                    if character is not None:
                        Notification.objects.filter(
                            pk=notification.id,
                        ).delete()

                        Contract.objects.create(
                            id=contract["contract_id"],
                            program=notification.program_location.program,
                            character=character,
                            total=contract["price"],
                            date=contract["date_issued"],
                        )

    def update_offices_esi(self):
        token = self.token(
            [
                "esi-universe.read_structures.v1",
                "esi-assets.read_corporation_assets.v1",
            ]
        )[0]

        assets = esi_fetch(
            "Assets.get_corporations_corporation_id_assets",
            args={
                "corporation_id": self.corporation.corporation_id,
            },
            has_pages=True,
            token=token,
        )

        office_ids_to_remove = list(
            Office.objects.filter(corporation=self).values_list("id", flat=True)
        )

        for asset in assets:
            if asset["type_id"] == OFFICE_TYPE_ID:
                location = Location.objects.get_or_create_from_esi(
                    location_id=asset["location_id"],
                    token=token,
                )[0]

                office_id = asset["item_id"]
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
            logger.error("Invalid token for fetching information")
            error = self.ERROR_TOKEN_INVALID
        except TokenExpiredError:
            logger.error("Token expired for fetching information")
            error = self.ERROR_TOKEN_EXPIRED
        else:
            if not token:
                logger.error("No token found with sufficient scopes")
                error = self.ERROR_TOKEN_INVALID

        return token, error

    def _logger_prefix(self):
        """returns standard logger prefix function"""
        return make_logger_prefix(self.corporation.corporation_ticker)

    def __str__(self):
        return self.corporation.corporation_name


class Location(models.Model):
    """An Eve Online buyback location: station or Upwell structure"""

    CATEGORY_STATION_ID = 3
    CATEGORY_STRUCTURE_ID = 65
    CATEGORY_UNKNOWN_ID = 0
    CATEGORY_CHOICES = [
        (CATEGORY_STATION_ID, "station"),
        (CATEGORY_STRUCTURE_ID, "structure"),
        (CATEGORY_UNKNOWN_ID, "(unknown)"),
    ]

    id = models.PositiveBigIntegerField(
        help_text="Eve Online location ID",
        primary_key=True,
    )
    name = models.CharField(
        max_length=100, help_text="In-game name of this station or structure"
    )
    eve_solar_system = models.ForeignKey(
        EveSolarSystem,
        blank=True,
        default=None,
        null=True,
        on_delete=models.deletion.SET_DEFAULT,
        related_name="+",
    )
    category_id = models.IntegerField(
        choices=CATEGORY_CHOICES,
        default=CATEGORY_UNKNOWN_ID,
    )

    objects = LocationManager()

    class Meta:
        default_permissions = ()

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

    id = models.PositiveBigIntegerField(
        primary_key=True,
        help_text="Item ID of the office",
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

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.location.name


class Program(models.Model):
    """An Eve Online buyback program for a corp"""

    id = models.AutoField(
        auto_created=True,
        primary_key=True,
        verbose_name="ID",
    )
    corporation = models.ForeignKey(
        Corporation,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    name = models.CharField(
        max_length=100,
    )

    class Meta:
        default_permissions = ()


class ProgramItem(models.Model):
    """Items in the buyback program for a corp"""

    id = models.AutoField(
        auto_created=True,
        primary_key=True,
        verbose_name="ID",
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    item_type = models.ForeignKey(
        EveType,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    brokerage = models.IntegerField(
        help_text="Jita max buy - x%",
        validators=[validate_brokerage],
    )
    use_refined_value = models.BooleanField(
        help_text="If ore, calculate on top of refined value",
    )

    class Meta:
        default_permissions = ()
        unique_together = ["program", "item_type"]


class ProgramLocation(models.Model):
    """Locations for buyback program for a corp"""

    id = models.AutoField(
        auto_created=True,
        primary_key=True,
        verbose_name="ID",
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    office = models.ForeignKey(
        Office,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )

    def __str__(self):
        return self.office.location.name

    class Meta:
        default_permissions = ()
        unique_together = ["program", "office"]


class Notification(models.Model):
    """Notifiaction by user that he is sending contract"""

    id = models.AutoField(
        auto_created=True,
        primary_key=True,
        verbose_name="ID",
    )
    program_location = models.ForeignKey(
        ProgramLocation,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    total = models.PositiveBigIntegerField(
        help_text="Total value of contract",
    )
    items = models.TextField(
        help_text="JSON dump of item data",
    )

    class Meta:
        default_permissions = ()


class Contract(models.Model):
    """Contract that is accepted in the buyback program"""

    id = models.PositiveBigIntegerField(
        primary_key=True,
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    character = models.ForeignKey(
        CharacterOwnership,
        on_delete=models.deletion.CASCADE,
        related_name="+",
    )
    total = models.PositiveBigIntegerField(
        help_text="Total value of contract",
    )
    date = models.DateTimeField()

    class Meta:
        default_permissions = ()
