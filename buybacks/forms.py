from django import forms
from eveuniverse.models import EveType

from .models import Office
from .validators import validate_brokerage


class ProgramForm(forms.Form):
    name = forms.CharField(
        label="Program Name",
        help_text="Give your buyback program a name to easily identify it",
    )


class ProgramItemForm(forms.Form):
    item_type = forms.ModelChoiceField(
        queryset=EveType.objects.filter(published=True),
        label="Item type",
        help_text="Add the item type which is accepted in this buyback program",
        empty_label=None,
    )
    brokerage = forms.IntegerField(
        label="Brokerage",
        help_text="Set the % corporation gets on top of 'Jita Max Buy'",
        validators=[validate_brokerage],
    )
    use_refined_value = forms.BooleanField(
        label="Calculate value using the refined end product (only works for ore)",
        required=False,
    )


class ProgramLocationForm(forms.Form):
    office = forms.ModelChoiceField(
        queryset=Office.objects,
        label="Location",
        help_text="Add the location where buybacks in this program are accepted",
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)

        super(ProgramLocationForm, self).__init__(*args, **kwargs)

        self.fields['office'].queryset = Office.objects.filter(
            corporation=program.corporation,
        )
