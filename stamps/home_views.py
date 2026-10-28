"""T5 home page and read-only Stamp feed."""
from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.http import require_safe

from .models import Stamp
from .views import email_verified

#allows safe requests to home page
@require_safe
def home(request):
    # Reuse T3 allauth verification, not v004 authentication.
    allowed = email_verified(request.user)
    stamps = []

    #loads Stamps for verified users
    if allowed:
        stamps = (
            Stamp.objects.select_related('creator')
            .annotate(participant_count=Count('stampparticipation'))
            .order_by('date', 'time', 'pk')
        )

    #renders home page with Stamp data
    return render(request, 'stamps/home.html', {
        'stamps': stamps, 'allowed': allowed,
    })
