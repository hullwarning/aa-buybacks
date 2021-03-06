from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from esi.decorators import token_required
from eveuniverse.models import EveType

from ..models import Corporation, Program
from ..tasks import update_offices_for_corp
from ..utils import MessagesPlus


@login_required
def index(request):
    context = {"programs": Program.objects.filter()}

    return render(request, "buybacks2/index.html", context)


@login_required
@permission_required("buybacks2.manage_programs")
def item_autocomplete(request):
    items = EveType.objects.filter(published=True).exclude(
        eve_group__eve_category__id=9
    )

    q = request.GET.get("q", None)

    if q is not None:
        items = items.filter(name__icontains=q)

    items = items.annotate(
        value=F("id"),
        text=F("name"),
    ).values("value", "text")

    return JsonResponse(list(items), safe=False)


@login_required
@permission_required("buybacks2.setup_retriever")
@token_required(
    scopes=[
        "esi-universe.read_structures.v1",
        "esi-assets.read_corporation_assets.v1",
        "esi-contracts.read_corporation_contracts.v1",
    ]
)
def setup(request, token):
    success = True
    owned_char = None
    token_char = EveCharacter.objects.get(character_id=token.character_id)

    try:
        owned_char = CharacterOwnership.objects.get(
            user=request.user, character=token_char
        )
    except CharacterOwnership.DoesNotExist:
        MessagesPlus.error(
            request,
            format_html(
                gettext_lazy(
                    "You can only use your main or alt characters to add corporations. "
                    "However, character %s is neither. "
                )
                % format_html("<strong>{}</strong>", token_char.character_name)
            ),
        )
        success = False

    if success:
        try:
            corporation = EveCorporationInfo.objects.get(
                corporation_id=token_char.corporation_id
            )
        except EveCorporationInfo.DoesNotExist:
            corporation = EveCorporationInfo.objects.create_corporation(
                token_char.corporation_id
            )

        with transaction.atomic():
            corp, _ = Corporation.objects.update_or_create(
                corporation=corporation, character=owned_char
            )

            corp.save()

        update_offices_for_corp.delay(corp_pk=corp.pk)

        MessagesPlus.info(
            request,
            format_html(
                gettext_lazy(
                    "%(corporation)s has been added with %(character)s "
                    "as sync character. We have started fetching offices "
                    "for this corporation. You will receive a report once "
                    "the process is finished."
                )
                % {
                    "corporation": format_html("<strong>{}</strong>", corp),
                    "character": format_html(
                        "<strong>{}</strong>", corp.character.character.character_name
                    ),
                }
            ),
        )

    return redirect("buybacks2:index")
