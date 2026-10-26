from django import forms
from .models import Stamp

class StampForm(forms.ModelForm):
    class Meta:
        model = Stamp
        fields = [
            "title",
            "desc",
            "date",
            "time",
            "location",
            "cost",
            "max_participants",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter title",
            }),
            "desc": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "time": forms.TimeInput(attrs={
                "class": "form-control",
                "placeholder": "Enter time"
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter location",
            }),
            "cost": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter attendance cost",
            }),
            "max_participants": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter maximum occupancy",
            }),
        }
