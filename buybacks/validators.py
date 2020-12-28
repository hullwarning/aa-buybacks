from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy


def validate_brokerage(value):
    if value > 100 or value < 0:
        raise ValidationError(
            gettext_lazy("%(value)s is not a valid brokerage"),
            params={"value": value},
        )
