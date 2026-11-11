"""T5 home page and read-only Stamp feed."""
from django.db.models import Count, F, Q
from django.shortcuts import render
from django.views.decorators.http import require_safe
from django.utils import timezone

from .models import Stamp
from .forms import StampSearchForm
from .views import email_verified

#allows safe requests to home page
@require_safe
def home(request):

    current_date = timezone.localdate()
    current_time = timezone.localtime().time().replace(tzinfo=None)

    #deletes Stamps that have already expired
    Stamp.objects.filter(Q(date__lt=current_date) | Q(date=current_date, end_time__lte=current_time)).delete()
    # Reuse T3 allauth verification.
    allowed = email_verified(request.user)
    stamps = []
    search_form = StampSearchForm(request.GET)

    #loads Stamps for verified users
    if allowed:
        current_date = timezone.localdate()
        current_time = timezone.localtime().time().replace(tzinfo=None)

        stamps = (
            Stamp.objects.select_related('creator')
            .annotate(participant_count=Count('stampparticipation'))
            .filter(
                Q(date__gt=current_date)
                | Q(date=current_date, end_time__isnull=True)
                | Q(date=current_date, end_time__gt=current_time)
            )
            .order_by('date', 'time', 'pk')
        )
        if search_form.is_valid():
            filters = search_form.cleaned_data
            if filters['q']:
                stamps = stamps.filter(
                    Q(title__icontains=filters['q']) | Q(desc__icontains=filters['q'])
                )
            if filters['category']:
                stamps = stamps.filter(category=filters['category'])
            if filters['date']:
                stamps = stamps.filter(date=filters['date'])
            if filters['location']:
                stamps = stamps.filter(location__icontains=filters['location'])
            if filters['max_cost'] is not None:
                stamps = stamps.filter(cost__lte=filters['max_cost'])
            if filters['available_only']:
                stamps = stamps.filter(participant_count__lt=F('max_participants'))
        else:
            # Show form errors.
            stamps = stamps.none()

    #renders home page with Stamp data
    return render(request, 'stamps/home.html', {
        'stamps': stamps, 'allowed': allowed, 'search_form': search_form,
    })
