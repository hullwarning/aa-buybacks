from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from ..models import Contract


@login_required
@permission_required("buybacks.basic_access")
def my_stats(request):
    contracts = Contract.objects.filter(
        character__user=request.user,
    )

    context = {
        "contracts": contracts,
        "show_user": False,
    }

    return render(request, "buybacks/stats.html", context)


@login_required
@permission_required("buybacks.manage_programs")
def program_stats(request, program_pk):
    contracts = Contract.objects.filter(
        program__pk=program_pk,
    )

    context = {
        "contracts": contracts,
        "show_user": True,
    }

    return render(request, "buybacks/stats.html", context)
