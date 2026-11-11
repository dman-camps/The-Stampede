from django import forms
from django.contrib.auth.models import User

from .models import Stamp


class StampSearchForm(forms.Form):
    q = forms.CharField(required=False, max_length=100, label='Keywords',
        widget=forms.TextInput(attrs={'placeholder': 'Search title or description'}))
    category = forms.ChoiceField(required=False,
        choices=[('', 'All categories')] + Stamp.CATEGORY_CHOICES)
    date = forms.DateField(required=False,
        widget=forms.DateInput(attrs={'type': 'date'}))
    location = forms.CharField(required=False, max_length=255, label='Campus location', widget=forms.Select())
    max_cost = forms.DecimalField(required=False, min_value=0,
        max_digits=8, decimal_places=2, label='Maximum cost ($)',
        widget=forms.NumberInput(attrs={'min': '0', 'step': '1'}))
    available_only = forms.BooleanField(required=False, label='Only Stamps with spots available')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        known = [value for value, label in StampForm.LOCATION_CHOICES if value and value != 'Other']
        existing = list(Stamp.objects.exclude(location='').values_list('location', flat=True).distinct().order_by('location'))
        choices = [('', 'All locations')] + [(value, value) for value in sorted(set(known + existing), key=str.casefold)]
        selected = self.data.get(self.add_prefix('location')) if self.is_bound else None
        if selected and selected not in {value for value, _ in choices}:
            choices.append((selected, selected))
        self.fields['location'].widget.choices = choices


class StampForm(forms.ModelForm):
    #defines available campus locations
    LOCATION_CHOICES = [
        ("", "Select a location"),
        ("Allwine Hall", "Allwine Hall"),
        ("Arts & Sciences Hall", "Arts & Sciences Hall"),
        ("Baxter Arena", "Baxter Arena"),
        ("Criss Library", "Criss Library"),
        ("Dodge Clubhouse", "Dodge Clubhouse"),
        ("Durham Science Center", "Durham Science Center"),
        ("Health & Kinesiology", "Health & Kinesiology"),
        ("Mammel Hall", "Mammel Hall"),
        ("Maverick Landing", "Maverick Landing"),
        ("Maverick Village", "Maverick Village"),
        ("Milo Bail Student Center", "Milo Bail Student Center"),
        ("Pep Bowl", "Pep Bowl"),
        ("Peter Kiewit Institute", "Peter Kiewit Institute"),
        ("Scott Crossing", "Scott Crossing"),
        ("Strauss Performing Arts Center", "Strauss Performing Arts Center"),
        ("Weber Fine Arts Building", "Weber Fine Arts Building"),
        ("Other", "Other"),
    ]

    #creates dropdown for campus locations
    location = forms.ChoiceField(
        choices=LOCATION_CHOICES,
        label="Location",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    #allows users to enter other location
    other_location = forms.CharField(
        required=False,
        label="Other:",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter location",
        }),
    )

    #allows users to specify an area
    specify_area = forms.CharField(
        required=False,
        label="Specify Area",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. (Room 200, In the Lobby)",
        }),
    )

    #sets required event time fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["time"].required = True
        self.fields["end_time"].required = True
        if self.instance and self.instance.pk and self.instance.location:
            raw = self.instance.location
            base, sep, area = raw.partition(" — ")
            known = {value for value, label in self.LOCATION_CHOICES}
            if base in known and base != "Other":
                self.initial["location"] = base
            else:
                self.initial["location"] = "Other"
                self.initial["other_location"] = base
            self.initial["specify_area"] = area if sep else ""

    #checks that cost is not negative
    def clean_cost(self):
        cost = self.cleaned_data.get("cost")

        if cost is not None and cost < 0:
            raise forms.ValidationError("Cost cannot be negative.")

        return cost

    #checks that participant limit is at least two
    def clean_max_participants(self):
        max_participants = self.cleaned_data.get("max_participants")

        if max_participants is not None and max_participants < 2:
            raise forms.ValidationError(
                "Maximum participants must be at least 2."
            )

        return max_participants

    #checks required custom location details
    def clean(self):
        cleaned_data = super().clean()
        location = cleaned_data.get("location")
        other_location = cleaned_data.get("other_location", "").strip()

        if location == "Other" and not other_location:
            self.add_error(
                "other_location",
                "Please specify the location."
            )

        return cleaned_data

    #saves location with optional area details
    def save(self, commit=True):
        instance = super().save(commit=False)

        location = self.cleaned_data["location"]

        if location == "Other":
            location = self.cleaned_data["other_location"].strip()

        area = self.cleaned_data.get("specify_area", "").strip()

        if area:
            location = f"{location} — {area}"

        instance.location = location

        if commit:
            instance.save()
            self.save_m2m()

        return instance

    #defines Stamp fields and form appearance
    class Meta:
        model = Stamp
        fields = [
            "title",
            "category",
            "desc",
            "date",
            "time",
            "end_time",
            "location",
            "cost",
            "max_participants",
        ]

        #sets labels shown on form
        labels = {
            "desc": "Description",
            "time": "Event Start",
            "end_time": "Event End",
        }

        #sets input styles and placeholders
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
                "type": "time",
            }),
            "end_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
            "cost": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter attendance cost",
                "step": "1",
                "min": "0",
            }),
            "max_participants": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter maximum occupancy",
            }),
        }

from allauth.account.forms import SignupForm as AllauthSignupForm

#customizes account registration form
class CustomSignupForm(AllauthSignupForm):

    #updates password confirmation label
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "password2" in self.fields:
            self.fields["password2"].label = "Reenter Password"
            self.fields["password2"].widget.attrs["placeholder"] = "Reenter Password"

    #checks that both passwords match
    def clean_password2(self):
        password2 = self.cleaned_data.get("password2")
        password1 = self.cleaned_data.get("password1")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        return password2

class AccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username"]
class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        from .models import UserProfile
        model = UserProfile
        fields = ['display_name', 'bio', 'interests', 'campus_location']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'A little about you...'}),
            'interests': forms.TextInput(attrs={'placeholder': 'Robotics, music, hiking'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.save(update_fields=['first_name', 'last_name'])
        return profile


class ReportForm(forms.Form):
    reason = forms.ChoiceField(choices=[
        ('misleading', 'Misleading or inaccurate information'),
        ('inappropriate', 'Inappropriate content'),
        ('spam', 'Spam or advertising'),
        ('unsafe', 'Safety concern'),
        ('other', 'Other'),
    ])
    details = forms.CharField(required=False, max_length=1000, widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Add details (optional)'}))
