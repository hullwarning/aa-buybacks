from django.contrib.auth.decorators import login_required, permission_required
from esi.decorators import token_required
from esi.models import Token
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCorporationInfo, EveCharacter
from django.db import transaction
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
from django.shortcuts import redirect, render

from .models import Corporation, Program, ProgramItem, ProgramLocation
from .utils import messages_plus
from .tasks import update_offices_for_corp
from .forms import ProgramForm, ProgramItemForm, ProgramLocationForm


ADD_PROGRAM_TOKEN_TAG = "buybacks_add_program_token"


@login_required
@permission_required('buybacks.basic_access')
def index(request):

    context = {
        'text': 'Hello, World!'
    }
    return render(request, 'buybacks/index.html', context)


@login_required
@permission_required('buybacks.manage_programs')
def program(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()

    if program is None:
        return redirect('buybacks:index')

    context = {
        'program': program,
        'items': ProgramItem.objects.filter(program=program),
        'locations': ProgramLocation.objects.filter(program=program),
        'corporation': program.corporation.corporation,
    }

    return render(request, 'buybacks/program.html', context)


@login_required
@permission_required('buybacks.manage_programs')
def program_remove(request, program_pk):
    Program.objects.filter(pk=program_pk).delete()

    return redirect('buybacks:index')


@login_required
@permission_required('buybacks.manage_programs')
def program_remove_item(request, program_pk, item_type_pk):
    ProgramItem.objects.filter(
        program=program_pk, item_type=item_type_pk,
    ).delete()

    return redirect('buybacks:program', program_pk=program_pk)


@login_required
@permission_required('buybacks.manage_programs')
def program_remove_location(request, program_pk, office_pk):
    ProgramLocation.objects.filter(
        program=program_pk, office=office_pk,
    ).delete()

    return redirect('buybacks:program', program_pk=program_pk)


@login_required
@permission_required('buybacks.manage_programs')
def program_add_item(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()

    if program is None:
        return redirect('buybacks:index')

    if request.method != 'POST':
        form = ProgramItemForm()
    else:
        form = ProgramItemForm(request.POST)

        if form.is_valid():
            item_type = form.cleaned_data['item_type']
            brokerage = form.cleaned_data['brokerage']
            use_refined_value = form.cleaned_data['use_refined_value']

            try:
                _, created = ProgramItem.objects.update_or_create(
                    item_type=item_type,
                    program=program,
                    defaults={
                        'brokerage': brokerage,
                        'use_refined_value': use_refined_value,
                    },
                )

                if created:
                    messages_plus.success(
                        request,
                        format_html(
                            'Added <strong>{}</strong> to <strong>{}</strong>',
                            item_type, program.name,
                        ),
                    )

                return redirect('buybacks:program', program_pk=program.id)

            except Exception:
                messages_plus.error(
                    request,
                    'Failed to add item to buyback program',
                )

    context = {
        'program': program,
        'corporation': program.corporation.corporation,
        'form': form,
    }

    return render(request, 'buybacks/program_add_item.html', context)


@login_required
@permission_required('buybacks.manage_programs')
def program_add_location(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()

    if program is None:
        return redirect('buybacks:index')

    if request.method != 'POST':
        form = ProgramLocationForm(program=program)
    else:
        form = ProgramLocationForm(request.POST, program=program)

        if form.is_valid():
            office = form.cleaned_data['office']

            try:
                _, created = ProgramLocation.objects.update_or_create(
                    office=office, program=program
                )

                if created:
                    messages_plus.success(
                        request,
                        format_html(
                            'Added <strong>{}</strong> to <strong>{}</strong>',
                            office, program.name,
                        ),
                    )

                return redirect('buybacks:program', program_pk=program.id)

            except Exception:
                messages_plus.error(
                    request,
                    'Failed to add location to buyback program',
                )

    context = {
        'program': program,
        'corporation': program.corporation.corporation,
        'form': form,
    }

    return render(request, 'buybacks/program_add_location.html', context)


@login_required
@token_required(
    scopes=[
        'publicData',
    ]
)
@permission_required('buybacks.manage_programs')
def program_add(request, token):
    request.session[ADD_PROGRAM_TOKEN_TAG] = token.pk
    return redirect("buybacks:program_add_2")


@login_required
@permission_required('buybacks.manage_programs')
def program_add_2(request):
    if ADD_PROGRAM_TOKEN_TAG not in request.session:
        raise RuntimeError("Missing token in session")
    else:
        token = Token.objects.get(pk=request.session[ADD_PROGRAM_TOKEN_TAG])

    success = True
    token_char = EveCharacter.objects.get(character_id=token.character_id)

    try:
        corporation = Corporation.objects.get(
            corporation=token_char.corporation
        )
    except (Corporation.DoesNotExist, EveCorporationInfo.DoesNotExist):
        messages_plus.error(
            request,
            format_html(
                gettext_lazy(
                    "You need to setup your corp first before managing it's "
                    "buyback programs"
                )
            ),
        )
        success = False

    if success:
        if request.method != 'POST':
            form = ProgramForm()
        else:
            form = ProgramForm(request.POST)

            if form.is_valid():
                name = form.cleaned_data['name']

                try:
                    program = Program.objects.create(
                        name=name, corporation=corporation
                    )
                    messages_plus.success(
                        request,
                        format_html(
                            'Created buyback program <strong>{}</strong>',
                            program.name,
                        ),
                    )
                    return redirect('buybacks:program', program_pk=program.id)

                except Exception:
                    messages_plus.error(
                        request,
                        'Failed to create buyback program',
                    )

        context = {
            'corporation': corporation.corporation,
            'form': form,
        }

        return render(request, 'buybacks/program_add.html', context)

    return redirect('buybacks:index')


@login_required
@token_required(
    scopes=[
        'publicData',
    ]
)
@permission_required('buybacks.manage_programs')
def manage(request, token):
    success = True
    token_char = EveCharacter.objects.get(character_id=token.character_id)

    try:
        corporation = Corporation.objects.get(
            corporation=token_char.corporation
        )
    except (Corporation.DoesNotExist, EveCorporationInfo.DoesNotExist):
        messages_plus.error(
            request,
            format_html(
                gettext_lazy(
                    "You need to setup your corp first before managing it's "
                    "buyback programs"
                )
            ),
        )
        success = False

    if success:
        context = {
            'programs': Program.objects.filter(
                corporation=corporation
            ),
            'corporation': corporation.corporation,
        }

        return render(request, 'buybacks/manage.html', context)

    return redirect('buybacks:index')


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
