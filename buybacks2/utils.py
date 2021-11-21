import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.constants import DEBUG, ERROR, INFO, SUCCESS, WARNING
from django.utils.html import format_html

from allianceauth.services.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class LoggerAddTag(logging.LoggerAdapter):
    """
    add custom tag to a logger
    """

    def __init__(self, my_logger, prefix):
        super().__init__(my_logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        """
        process log items
        :param msg:
        :param kwargs:
        :return:
        """

        return f"[{self.prefix}] {msg}", kwargs


def make_logger_prefix(tag: str):
    """creates a function to add logger prefix, which returns tag with empty"""
    return lambda text="": f"{tag}{(': ' + text) if text else ''}"


class MessagesPlus:
    """Pendant to Django messages adding level icons and HTML support

    Careful: Use with safe strings only
    """

    _glyph_map = {
        DEBUG: "eye-open",
        INFO: "info-sign",
        SUCCESS: "ok-sign",
        WARNING: "exclamation-sign",
        ERROR: "alert",
    }

    @classmethod
    def _add_messages_icon(cls, level: int, message: str) -> str:
        """Adds an level based icon to standard Django messages"""
        if level not in cls._glyph_map:
            raise ValueError("glyph for level not defined")
        else:
            glyph = cls._glyph_map[level]

        return format_html(
            '<span class="glyphicon glyphicon-{}" '
            'aria-hidden="true"></span>&nbsp;&nbsp;{}',
            glyph,
            message,
        )

    @classmethod
    def debug(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.debug(
            request, cls._add_messages_icon(DEBUG, message), extra_tags, fail_silently
        )

    @classmethod
    def info(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.info(
            request, cls._add_messages_icon(INFO, message), extra_tags, fail_silently
        )

    @classmethod
    def success(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.success(
            request, cls._add_messages_icon(SUCCESS, message), extra_tags, fail_silently
        )

    @classmethod
    def warning(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.warning(
            request, cls._add_messages_icon(WARNING, message), extra_tags, fail_silently
        )

    @classmethod
    def error(
        cls,
        request: object,
        message: str,
        extra_tags: str = "",
        fail_silently: bool = False,
    ):
        messages.error(
            request, cls._add_messages_icon(ERROR, message), extra_tags, fail_silently
        )


def clean_setting(
    name: str,
    default_value: object,
    min_value: int = None,
    max_value: int = None,
    required_type: type = None,
):
    """cleans the input for a custom setting

    Will use `default_value` if settings does not exit or has the wrong type
    or is outside define boundaries (for int only)

    Need to define `required_type` if `default_value` is `None`

    Will assume `min_value` of 0 for int (can be overriden)

    Returns cleaned value for setting
    """
    if default_value is None and not required_type:
        raise ValueError("You must specify a required_type for None defaults")

    if not required_type:
        required_type = type(default_value)

    if min_value is None and required_type == int:
        min_value = 0

    if not hasattr(settings, name):
        cleaned_value = default_value
    else:
        if (
            isinstance(getattr(settings, name), required_type)
            and (min_value is None or getattr(settings, name) >= min_value)
            and (max_value is None or getattr(settings, name) <= max_value)
        ):
            cleaned_value = getattr(settings, name)
        else:
            logger.warning(
                "You setting for %s it not valid. Please correct it. "
                "Using default for now: %s",
                name,
                default_value,
            )
            cleaned_value = default_value
    return cleaned_value
