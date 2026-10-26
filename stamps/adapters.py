from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError


class UNOAccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        email = super().clean_email(email).strip().lower()
        if not email.endswith('@unomaha.edu'):
            raise ValidationError('Enter an address ending exactly in @unomaha.edu.')
        return email
