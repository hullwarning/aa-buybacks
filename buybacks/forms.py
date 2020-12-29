from django import forms
from eveuniverse.models import EveType

from .models import Office, ProgramLocation
from .validators import validate_brokerage


class ProgramForm(forms.Form):
    name = forms.CharField(
        label="Program Name",
        help_text="Give your buyback program a name to easily identify it",
    )


class ProgramItemForm(forms.Form):
    item_type = forms.ModelChoiceField(
        queryset=EveType.objects.none(),
        label="Item type",
        help_text="Add the name of item which is accepted in this buyback program. Once you start typing, we offer suggestions",
        empty_label=None,
    )
    brokerage = forms.IntegerField(
        label="Brokerage",
        help_text="Set the percentage corporation gets on top of 'Jita Max Buy'",
        validators=[validate_brokerage],
    )
    use_refined_value = forms.BooleanField(
        label="Calculate value using the refined end product (only works for ore)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        value = kwargs.pop('value', None)

        super(ProgramItemForm, self).__init__(*args, **kwargs)

        if value is not None:
            self.fields['item_type'].queryset = EveType.objects.filter(
                pk=value, published=True,
            ).exclude(eve_group__eve_category__id=9)


class ProgramLocationForm(forms.Form):
    office = forms.ModelChoiceField(
        queryset=Office.objects.none(),
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


class CalculatorForm(forms.Form):
    office = forms.ModelChoiceField(
        queryset=ProgramLocation.objects.none(),
        label="Location",
        help_text="Structure or station from where you want to sell items",
        empty_label=None,
    )
    items = forms.CharField(
        widget=forms.Textarea,
        label="Items",
        help_text="Copy and paste the item data from your inventory. Item types not in this buyback program will be ignored",
    )

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)

        super(CalculatorForm, self).__init__(*args, **kwargs)

        self.fields['office'].queryset = ProgramLocation.objects.filter(
            program=program,
        )
