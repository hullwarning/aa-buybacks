import math

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
from django.urls import reverse
from esi.models import Token
from esi.decorators import token_required
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from ..helpers import evemarketer
from ..models import Program, ProgramItem, ProgramLocation, Corporation
from ..forms import ProgramForm, ProgramItemForm, ProgramLocationForm, CalculatorForm
from ..utils import messages_plus

ADD_PROGRAM_TOKEN_TAG = "buybacks_add_program_token"


@login_required
@permission_required("buybacks.basic_access")
def program_calculate(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()
    data = {}
    value = {}
    typeids = {}
    program_location = None
    total = 0

    if program is None:
        return redirect("buybacks:index")

    if request.method != "POST":
        form = CalculatorForm(program=program)
    else:
        form = CalculatorForm(request.POST, program=program)

        if form.is_valid():
            office = form.cleaned_data["office"]
            items = form.cleaned_data["items"]

            program_location = ProgramLocation.objects.filter(
                program=program,
                office__location__name=office,
            ).first()

            for item in items.split("\n"):

                parts = item.split("\t")

                if len(parts) >= 2:
                    name = parts[0]

                    quantity = int(
                        parts[1].replace(" ", "").replace(".", "").replace("\xa0", "")
                    )

                    if name in data:
                        data[name] += quantity
                    else:
                        data[name] = quantity

            brokerages = {}

            program_items = ProgramItem.objects.filter(
                program=program, item_type__name__in=data.keys()
            )

            for item in program_items:
                if not item.use_refined_value:
                    brokerages[item.item_type.name] = item.brokerage
                    typeids[item.item_type.name] = item.item_type.id

            prices = evemarketer(typeids.values())

            for name in brokerages:
                item_value = (
                    (100 - brokerages[name])
                    / 100
                    * data[name]
                    * prices[typeids[name]]["buy"]
                )

                value[name] = item_value
                total += item_value

            total = math.ceil(total)

    context = {
        "program": program,
        "corporation": program.corporation.corporation,
        "form": form,
        "data": data,
        "value": value,
        "typeids": typeids,
        "total": total,
        "program_location": program_location,
    }

    return render(request, "buybacks/program_calculate.html", context)


@login_required
@permission_required("buybacks.basic_access")
def program(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()

    if program is None:
        return redirect("buybacks:index")

    context = {
        "program": program,
        "items": ProgramItem.objects.filter(program=program),
        "locations": ProgramLocation.objects.filter(program=program),
        "corporation": program.corporation.corporation,
    }

    return render(request, "buybacks/program.html", context)


@login_required
@permission_required("buybacks.manage_programs")
def program_remove(request, program_pk):
    Program.objects.filter(pk=program_pk).delete()

    return redirect("buybacks:index")


@login_required
@permission_required("buybacks.manage_programs")
def program_remove_item(request, program_pk, item_type_pk):
    ProgramItem.objects.filter(
        program=program_pk,
        item_type=item_type_pk,
    ).delete()

    return redirect("buybacks:program", program_pk=program_pk)


@login_required
@permission_required("buybacks.manage_programs")
def program_remove_location(request, program_pk, office_pk):
    ProgramLocation.objects.filter(
        program=program_pk,
        office=office_pk,
    ).delete()

    return redirect("buybacks:program", program_pk=program_pk)


@login_required
@permission_required("buybacks.manage_programs")
def program_add_item(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()

    if program is None:
        return redirect("buybacks:index")

    if request.method != "POST":
        form = ProgramItemForm()
    else:
        form = ProgramItemForm(
            request.POST,
            value=int(request.POST["item_type"]),
        )

        if form.is_valid():
            item_type = form.cleaned_data["item_type"]
            brokerage = form.cleaned_data["brokerage"]
            use_refined_value = form.cleaned_data["use_refined_value"]

            try:
                _, created = ProgramItem.objects.update_or_create(
                    item_type=item_type,
                    program=program,
                    defaults={
                        "brokerage": brokerage,
                        "use_refined_value": use_refined_value,
                    },
                )

                if created:
                    messages_plus.success(
                        request,
                        format_html(
                            "Added <strong>{}</strong> to <strong>{}</strong>",
                            item_type,
                            program.name,
                        ),
                    )

                return redirect("buybacks:program", program_pk=program.id)

            except Exception:
                messages_plus.error(
                    request,
                    "Failed to add item to buyback program",
                )

    context = {
        "program": program,
        "corporation": program.corporation.corporation,
        "form": form,
    }

    return render(request, "buybacks/program_add_item.html", context)


@login_required
@permission_required("buybacks.manage_programs")
def program_add_location(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()

    if program is None:
        return redirect("buybacks:index")

    if request.method != "POST":
        form = ProgramLocationForm(program=program)
    else:
        form = ProgramLocationForm(request.POST, program=program)

        if form.is_valid():
            office = form.cleaned_data["office"]

            try:
                _, created = ProgramLocation.objects.update_or_create(
                    office=office, program=program
                )

                if created:
                    messages_plus.success(
                        request,
                        format_html(
                            "Added <strong>{}</strong> to <strong>{}</strong>",
                            office,
                            program.name,
                        ),
                    )

                return redirect("buybacks:program", program_pk=program.id)

            except Exception:
                messages_plus.error(
                    request,
                    "Failed to add location to buyback program",
                )

    context = {
        "program": program,
        "corporation": program.corporation.corporation,
        "form": form,
    }

    return render(request, "buybacks/program_add_location.html", context)


@login_required
@token_required(
    scopes=[
        "publicData",
    ]
)
@permission_required("buybacks.manage_programs")
def program_add(request, token):
    request.session[ADD_PROGRAM_TOKEN_TAG] = token.pk
    return redirect("buybacks:program_add_2")


@login_required
@permission_required("buybacks.manage_programs")
def program_add_2(request):
    if ADD_PROGRAM_TOKEN_TAG not in request.session:
        raise RuntimeError("Missing token in session")
    else:
        token = Token.objects.get(pk=request.session[ADD_PROGRAM_TOKEN_TAG])

    success = True
    token_char = EveCharacter.objects.get(character_id=token.character_id)

    try:
        corporation = Corporation.objects.get(corporation=token_char.corporation)
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
        if request.method != "POST":
            form = ProgramForm()
        else:
            form = ProgramForm(request.POST)

            if form.is_valid():
                name = form.cleaned_data["name"]

                try:
                    program = Program.objects.create(name=name, corporation=corporation)
                    messages_plus.success(
                        request,
                        format_html(
                            "Created buyback program <strong>{}</strong>",
                            program.name,
                        ),
                    )
                    return redirect("buybacks:program", program_pk=program.id)

                except Exception:
                    messages_plus.error(
                        request,
                        "Failed to create buyback program",
                    )

        context = {
            "corporation": corporation.corporation,
            "form": form,
            "to": reverse("buybacks:program_add_2"),
            "action": "Create",
        }

        return render(request, "buybacks/program_add.html", context)

    return redirect("buybacks:index")


@login_required
@permission_required("buybacks.manage_programs")
def program_edit(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()

    if program is None:
        return redirect("buybacks:index")

    if request.method != "POST":
        form = ProgramForm(program=program)
    else:
        form = ProgramForm(request.POST, program=program)

        if form.is_valid():
            program.name = form.cleaned_data["name"]

            try:
                program.save()
                messages_plus.success(
                    request,
                    format_html(
                        "Edited buyback program <strong>{}</strong>",
                        program.name,
                    ),
                )
                return redirect("buybacks:program", program_pk=program.id)

            except Exception:
                messages_plus.error(
                    request,
                    "Failed to edit buyback program",
                )

    context = {
        "corporation": program.corporation.corporation,
        "form": form,
        "to": reverse(
            "buybacks:program_edit",
            kwargs={
                "program_pk": program_pk,
            },
        ),
        "action": "Edit",
    }

    return render(request, "buybacks/program_add.html", context)
