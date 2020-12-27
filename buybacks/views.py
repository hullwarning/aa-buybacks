from django.contrib.auth.decorators import login_required, permission_required
from esi.decorators import token_required
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCorporationInfo, EveCharacter
from django.db import transaction
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
from django.shortcuts import redirect, render

from .models import Corporation
from .utils import messages_plus
from .tasks import update_offices_for_corp


@login_required
@permission_required('buybacks.basic_access')
def index(request):

    context = {
        'text': 'Hello, World!'
    }
    return render(request, 'buybacks/index.html', context)


@login_required
@permission_required('buybacks.manage_programs')
def manage(request):

    context = {
        'text': 'Hello, World!'
    }
    return render(request, 'buybacks/index.html', context)


@login_required
@permission_required('buybacks.setup_retriever')
@token_required(
    scopes=[
        'esi-universe.read_structures.v1',
        'esi-assets.read_corporation_assets.v1',
    ]
)
def setup(request, token):
    success = True
    token_char = EveCharacter.objects.get(character_id=token.character_id)

    try:
        owned_char = CharacterOwnership.objects.get(
            user=request.user, character=token_char
        )
    except CharacterOwnership.DoesNotExist:
        messages_plus.error(
            request,
            format_html(
                gettext_lazy(
                    "You can only use your main or alt characters "
                    "to add corporations. "
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
        messages_plus.info(
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

    return redirect("buybacks:manage")
