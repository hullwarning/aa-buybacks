import json

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import format_html

from eveuniverse.models import EveType

from ..models import Notification, Program, ProgramLocation
from ..utils import messages_plus


@csrf_exempt
@login_required
@permission_required("buybacks.basic_access")
def program_notify(request, program_pk):
    program = Program.objects.filter(pk=program_pk).first()

    if request.method != "POST" or program is None:
        return HttpResponseBadRequest("")

    data = json.loads(request.body)

    program_location = ProgramLocation.objects.filter(
        program=program, id=data["program_location"]
    ).first()

    if program_location is None:
        return HttpResponseBadRequest("")

    notification = Notification.objects.create(
        program_location=program_location,
        user=request.user,
        total=data["total"],
        items=json.dumps(data["items"]),
    )

    if notification is None:
        return HttpResponseBadRequest("")
    else:
        messages_plus.success(
            request,
            format_html(
                "Created a notification for buyback program <strong>{}</strong>",
                program.name,
            ),
        )

    return JsonResponse({})


@login_required
@permission_required("buybacks.basic_access")
def my_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user,
    )

    typeids = set()
    items = {}

    for notification in notifications:
        data = json.loads(notification.items)

        for type_id in data:
            typeids.add(type_id)

    types = EveType.objects.filter(pk__in=typeids)

    for item in types:
        items[str(item.id)] = item.name

    context = {
        "bb_notifications": notifications,
        "items": items,
        "remove_url": "buybacks:notification_remove",
        "show_user": False,
    }

    return render(request, "buybacks/notifications.html", context)


@login_required
@permission_required("buybacks.basic_access")
def notification_remove(request, notification_pk, program_pk):
    Notification.objects.filter(
        pk=notification_pk,
        user=request.user,
        program_location__program__id=program_pk,
    ).delete()

    return redirect("buybacks:my_notifications")


@login_required
@permission_required("buybacks.manage_programs")
def program_notifications(request, program_pk):
    notifications = Notification.objects.filter(
        program_location__program__id=program_pk,
    )

    typeids = set()
    items = {}

    for notification in notifications:
        data = json.loads(notification.items)

        for type_id in data:
            typeids.add(type_id)

    types = EveType.objects.filter(pk__in=typeids)

    for item in types:
        items[str(item.id)] = item.name

    context = {
        "bb_notifications": notifications,
        "items": items,
        "remove_url": "buybacks:program_notification_remove",
        "show_user": True,
    }

    return render(request, "buybacks/notifications.html", context)


@login_required
@permission_required("buybacks.manage_programs")
def program_notification_remove(request, notification_pk, program_pk):
    Notification.objects.filter(
        pk=notification_pk,
        program_location__program__id=program_pk,
    ).delete()

    return redirect("buybacks:program_notifications", program_pk=program_pk)
