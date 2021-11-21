import math
import re

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from esi.decorators import token_required
from esi.models import Token

from ..forms import CalculatorForm, ProgramForm, ProgramItemForm, ProgramLocationForm
from ..helpers import fuzzworkmarket_lookup
from ..models import Corporation, Program, ProgramItem, ProgramLocation
from ..utils import MessagesPlus

ADD_PROGRAM_TOKEN_TAG = "buybacks_add_program_token"


@login_required
@permission_required("buybacks2.basic_access")
def program_calculate(request, program_pk):
    bb_program = Program.objects.filter(pk=program_pk).first()
    data = dict()
    value = {}
    typeids = {}
    program_location = None
    total = 0

    if bb_program is None:
        return redirect("buybacks2:index")

    if request.method != "POST":
        form = CalculatorForm(program=bb_program)
    else:
        form = CalculatorForm(request.POST, program=bb_program)

        if form.is_valid():
            office = form.cleaned_data["office"]
            items = form.cleaned_data["items"]

            program_location = ProgramLocation.objects.filter(
                program=bb_program,
                office__location__name=office,
            ).first()

            # Fix From https://gitlab.com/pksunkara/aa-buybacks/-/issues/34 - https://gitlab.com/Wered
            for line in items.splitlines():
                line = " ".join(line.split()).replace(",", "")
                filtered = re.match(r"(.*?)([0-9]+)", line).groups
                name = filtered("1")[0].rstrip()
                quantity = filtered("1")[1]
                if name in data:
                    data[name] += int(quantity)
                else:
                    data[name] = int(quantity)

            brokerages = {}

            program_items = ProgramItem.objects.filter(
                program=bb_program, item_type__name__in=data.keys()
            )

            for item in program_items:
                if not item.use_refined_value:
                    brokerages[item.item_type.name] = item.brokerage
                    typeids[item.item_type.name] = item.item_type.id

            prices = fuzzworkmarket_lookup(typeids.values())

            for name in brokerages:
                item_value = (
                    (100 - brokerages[name])
                    / 100
                    * data[name]
                    * prices[typeids[name]]["buy"]
                )

                value[name]["unit_price"] = item_value
                value[name]["typeid"] = typeids[name]
                value[name]["quantity"] = data[name]
                value[name]["name"] = name
                total += item_value

            total = math.ceil(total)

    context = {
        "program": bb_program,
        "corporation": bb_program.corporation.corporation,
        "form": form,
        "value": value,
        "total": total,
        "program_location": program_location,
    }

    return render(request, "buybacks2/program_calculate.html", context)


@login_required
@permission_required("buybacks2.basic_access")
def program(request, program_pk):
    bb_program = Program.objects.filter(pk=program_pk).first()

    if bb_program is None:
        return redirect("buybacks2:index")

    context = {
        "program": bb_program,
        "items": ProgramItem.objects.filter(program=bb_program),
        "locations": ProgramLocation.objects.filter(program=bb_program),
        "corporation": bb_program.corporation.corporation,
    }

    return render(request, "buybacks2/program.html", context)


@login_required
@permission_required("buybacks2.manage_programs")
def program_remove(request, program_pk):
    Program.objects.filter(pk=program_pk).delete()

    return redirect("buybacks2:index")


@login_required
@permission_required("buybacks2.manage_programs")
def program_remove_item(request, program_pk, item_type_pk):
    ProgramItem.objects.filter(
        program=program_pk,
        item_type=item_type_pk,
    ).delete()

    return redirect("buybacks2:program", program_pk=program_pk)


@login_required
@permission_required("buybacks2.manage_programs")
def program_remove_location(request, program_pk, office_pk):
    ProgramLocation.objects.filter(
        program=program_pk,
        office=office_pk,
    ).delete()

    return redirect("buybacks2:program", program_pk=program_pk)


@login_required
@permission_required("buybacks2.manage_programs")
def program_add_item(request, program_pk):
    bb_program = Program.objects.filter(pk=program_pk).first()

    if bb_program is None:
        return redirect("buybacks2:index")

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
            use_refined_value = False
            # use_refined_value = form.cleaned_data["use_refined_value"]

            try:
                _, created = ProgramItem.objects.update_or_create(
                    item_type=item_type,
                    program=bb_program,
                    defaults={
                        "brokerage": brokerage,
                        "use_refined_value": use_refined_value,
                    },
                )

                if created:
                    MessagesPlus.success(
                        request,
                        format_html(
                            "Added <strong>{}</strong> to <strong>{}</strong>",
                            item_type,
                            bb_program.name,
                        ),
                    )

                return redirect("buybacks2:program", program_pk=bb_program.id)

            except Exception:
                MessagesPlus.error(
                    request,
                    "Failed to add item to buyback program",
                )

    context = {
        "program": bb_program,
        "corporation": bb_program.corporation.corporation,
        "form": form,
    }

    return render(request, "buybacks2/program_add_item.html", context)


@login_required
@permission_required("buybacks2.manage_programs")
def program_add_location(request, program_pk):
    bb_program = Program.objects.filter(pk=program_pk).first()

    if bb_program is None:
        return redirect("buybacks2:index")

    if request.method != "POST":
        form = ProgramLocationForm(program=bb_program)
    else:
        form = ProgramLocationForm(request.POST, program=bb_program)

        if form.is_valid():
            office = form.cleaned_data["office"]

            try:
                _, created = ProgramLocation.objects.update_or_create(
                    office=office, program=bb_program
                )

                if created:
                    MessagesPlus.success(
                        request,
                        format_html(
                            "Added <strong>{}</strong> to <strong>{}</strong>",
                            office,
                            bb_program.name,
                        ),
                    )

                return redirect("buybacks2:program", program_pk=bb_program.id)

            except Exception:
                MessagesPlus.error(
                    request,
                    "Failed to add location to buyback program",
                )

    context = {
        "program": bb_program,
        "corporation": bb_program.corporation.corporation,
        "form": form,
    }

    return render(request, "buybacks2/program_add_location.html", context)


@login_required
@token_required(
    scopes=[
        "publicData",
    ]
)
@permission_required("buybacks2.manage_programs")
def program_add(request, token):
    request.session[ADD_PROGRAM_TOKEN_TAG] = token.pk
    return redirect("buybacks2:program_add_2")


@login_required
@permission_required("buybacks2.manage_programs")
def program_add_2(request):
    if ADD_PROGRAM_TOKEN_TAG not in request.session:
        raise RuntimeError("Missing token in session")
    else:
        token = Token.objects.get(pk=request.session[ADD_PROGRAM_TOKEN_TAG])

    success = True
    corporation = None
    token_char = EveCharacter.objects.get(character_id=token.character_id)

    try:
        corporation = Corporation.objects.get(corporation=token_char.corporation)
    except (Corporation.DoesNotExist, EveCorporationInfo.DoesNotExist):
        MessagesPlus.error(
            request,
            format_html(
                gettext_lazy(
                    "You need to setup your corp first before managing it's buyback programs"
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
                    bb_program = Program.objects.create(
                        name=name, corporation=corporation
                    )
                    MessagesPlus.success(
                        request,
                        format_html(
                            "Created buyback program <strong>{}</strong>",
                            bb_program.name,
                        ),
                    )
                    return redirect("buybacks2:program", program_pk=bb_program.id)

                except Exception:
                    MessagesPlus.error(
                        request,
                        "Failed to create buyback program",
                    )

        context = {
            "corporation": corporation.corporation,
            "form": form,
            "to": reverse("buybacks2:program_add_2"),
            "action": "Create",
        }

        return render(request, "buybacks2/program_add.html", context)

    return redirect("buybacks2:index")


@login_required
@permission_required("buybacks2.manage_programs")
def program_edit(request, program_pk):
    bb_program = Program.objects.filter(pk=program_pk).first()

    if bb_program is None:
        return redirect("buybacks2:index")

    if request.method != "POST":
        form = ProgramForm(program=bb_program)
    else:
        form = ProgramForm(request.POST, program=bb_program)

        if form.is_valid():
            bb_program.name = form.cleaned_data["name"]

            try:
                bb_program.save()
                MessagesPlus.success(
                    request,
                    format_html(
                        "Edited buyback program <strong>{}</strong>",
                        bb_program.name,
                    ),
                )
                return redirect("buybacks2:program", program_pk=bb_program.id)

            except Exception:
                MessagesPlus.error(
                    request,
                    "Failed to edit buyback program",
                )

    context = {
        "corporation": bb_program.corporation.corporation,
        "form": form,
        "to": reverse(
            "buybacks2:program_edit",
            kwargs={
                "program_pk": program_pk,
            },
        ),
        "action": "Edit",
    }

    return render(request, "buybacks2/program_add.html", context)
