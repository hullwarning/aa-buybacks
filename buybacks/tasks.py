from bravado.exception import HTTPBadGateway, HTTPGatewayTimeout, HTTPServiceUnavailable
from celery import shared_task
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

from .models import Corporation
from .utils import LoggerAddTag
from . import __title__


DEFAULT_TASK_PRIORITY = 6
TASKS_TIME_LIMIT = 7200

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

# Create your tasks here
TASK_DEFAULT_KWARGS = {
    "time_limit": TASKS_TIME_LIMIT,
}

TASK_ESI_KWARGS = {
    **{
        "bind": True,
        "autoretry_for": (
            OSError,
            HTTPBadGateway,
            HTTPGatewayTimeout,
            HTTPServiceUnavailable,
        ),
        "retry_kwargs": {"max_retries": 3},
        "retry_backoff": 30,
    },
}


@shared_task(
    **{
        **TASK_ESI_KWARGS,
        **{
            "base": QueueOnce,
            "once": {"keys": ["corp_pk"], "graceful": True},
            "max_retries": None,
        },
    }
)
def update_offices_for_corp(self, corp_pk):
    """fetches all office locations for corp from ESI"""
    return _get_corp(corp_pk).update_offices_esi()


@shared_task(**TASK_DEFAULT_KWARGS)
def update_all_offices():
    for corp in Corporation.objects.all():
        update_offices_for_corp.apply_async(
            kwargs={"corp_pk": corp.pk},
            priority=DEFAULT_TASK_PRIORITY,
        )


@shared_task(
    **{
        **TASK_ESI_KWARGS,
        **{
            "base": QueueOnce,
            "once": {"keys": ["corp_pk"], "graceful": True},
            "max_retries": None,
        },
    }
)
def sync_contracts_for_corp(self, corp_pk):
    """fetches all contracts for corp from ESI"""
    return _get_corp(corp_pk).sync_contracts_esi()


@shared_task(**TASK_DEFAULT_KWARGS)
def sync_all_contracts():
    for corp in Corporation.objects.all():
        sync_contracts_for_corp.apply_async(
            kwargs={"corp_pk": corp.pk},
            priority=DEFAULT_TASK_PRIORITY,
        )


def _get_corp(corp_pk: int) -> Corporation:
    """returns the corp or raises exception"""
    try:
        corp = Corporation.objects.get(pk=corp_pk)
    except Corporation.DoesNotExist:
        raise Corporation.DoesNotExist(
            "Requested corp with pk {} does not exist".format(corp_pk)
        )
    return corp
