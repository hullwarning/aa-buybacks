from django.conf.urls import include, url

from .views import common, notifications, programs, stats

app_name = "buybacks2"

module_urls = [
    url(r"^/$", common.index, name="index"),
    url(r"^setup/$", common.setup, name="setup"),
    url(
        r"^item_autocomplete/$",
        common.item_autocomplete,
        name="item_autocomplete",
    ),
    url(
        r"^my_notifications/$", notifications.my_notifications, name="my_notifications"
    ),
    url(r"^my_stats/$", stats.my_stats, name="my_stats"),
    url(
        r"^notification/(?P<notification_pk>[0-9]+)/remove$",
        notifications.notification_remove,
        name="notification_remove",
    ),
    url(
        r"^notification/(?P<notification_pk>[0-9]+)/edit$",
        notifications.notification_edit,
        name="notification_edit",
    ),
    url(r"^program_add/$", programs.program_add, name="program_add"),
    url(r"^program_add_2/$", programs.program_add_2, name="program_add_2"),
    url(
        r"^program/(?P<program_pk>[0-9]+)/edit$",
        programs.program_edit,
        name="program_edit",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)$",
        programs.program,
        name="program",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/remove$",
        programs.program_remove,
        name="program_remove",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/calculate$",
        programs.program_calculate,
        name="program_calculate",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/stats$",
        stats.program_stats,
        name="program_stats",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/notify$",
        notifications.program_notify,
        name="program_notify",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/notifications$",
        notifications.program_notifications,
        name="program_notifications",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/add_item$",
        programs.program_add_item,
        name="program_add_item",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/add_location$",
        programs.program_add_location,
        name="program_add_location",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/remove_item/(?P<item_type_pk>[0-9]+)$",
        programs.program_remove_item,
        name="program_remove_item",
    ),
    url(
        r"^program/(?P<program_pk>[0-9]+)/remove_location/(?P<office_pk>[0-9]+)$",
        programs.program_remove_location,
        name="program_remove_location",
    ),
]

urlpatterns = [
    url(fr"^{app_name}/", include((module_urls, app_name), namespace=app_name)),
]
