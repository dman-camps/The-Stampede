
"""Home feed and dedicated event discovery."""
from functools import reduce
from operator import or_

from django.db.models import Count, F, Q
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_safe

from .models import Stamp, StampParticipation, UserFollow
from .forms import StampSearchForm
from .views import email_verified


#gets Stamps that have not expired
def _active_queryset():
    current_date = timezone.localdate()
    current_time = timezone.localtime().time().replace(tzinfo=None)

    return Stamp.objects.select_related('creator').annotate(
        participant_count=Count('stampparticipation')
    ).filter(
        Q(date__gt=current_date)
        | Q(date=current_date, end_time__isnull=True)
        | Q(date=current_date, end_time__gt=current_time)
    ).order_by('date', 'time', 'pk')


#applies search filters to Stamps
def _apply_filters(stamps, form):
    if form.is_valid():
        f = form.cleaned_data
        if f['q']:
            stamps = stamps.filter(
                Q(title__icontains=f['q'])
                | Q(desc__icontains=f['q'])
                | Q(location__icontains=f['q'])
            )
        if f['category']:
            stamps = stamps.filter(category=f['category'])
        if f['date']:
            stamps = stamps.filter(date=f['date'])
        if f['location']:
            stamps = stamps.filter(location__icontains=f['location'])
        if f['max_cost'] is not None:
            stamps = stamps.filter(cost__lte=f['max_cost'])
        if f['available_only']:
            stamps = stamps.filter(participant_count__lt=F('max_participants'))
    else:
        stamps = stamps.none()

    return stamps


@require_safe
def home(request):
    current_date = timezone.localdate()
    current_time = timezone.localtime().time().replace(tzinfo=None)

    #deletes Stamps that have already expired
    Stamp.objects.filter(
        Q(date__lt=current_date)
        | Q(date=current_date, end_time__lte=current_time)
    ).delete()

    allowed = email_verified(request.user)
    search_form = StampSearchForm(request.GET)
    context = {'allowed': allowed, 'stamps': [], 'search_form': search_form}

    if allowed:
        active_stamps = _active_queryset().filter(is_cancelled=False)

        context['stamps'] = _apply_filters(active_stamps, search_form)

        upcoming = active_stamps.filter(date__gte=current_date)

        followed_ids = UserFollow.objects.filter(
            follower=request.user
        ).values_list('followed_id', flat=True)

        followed_events = upcoming.filter(creator_id__in=followed_ids)[:4]

        joined_ids = StampParticipation.objects.filter(
            user=request.user
        ).values_list('stamp_id', flat=True)

        past_events = Stamp.objects.filter(pk__in=joined_ids)
        past_interests = list(
            past_events.values_list('category', flat=True).distinct()
        )
        past_locations = list(
            past_events.values_list('location', flat=True).distinct()
        )

        keywords = set()
        for title, description in past_events.values_list('title', 'desc'):
            keywords.update(
                word.strip('.,!?()[]{}:;').lower()
                for word in (title + ' ' + description).split()
                if len(word.strip('.,!?()[]{}:;')) >= 5
            )

        recommendation_terms = (
            Q(category__in=past_interests)
            | Q(location__in=past_locations)
        )

        keyword_query = reduce(
            or_,
            (
                Q(title__icontains=word)
                | Q(desc__icontains=word)
                | Q(location__icontains=word)
                for word in keywords
            ),
            Q()
        )

        if past_interests or past_locations or keywords:
            interest_events = upcoming.filter(
                recommendation_terms | keyword_query
            ).exclude(pk__in=joined_ids)[:4]
        else:
            interest_events = upcoming.none()

        context.update({
            'followed_events': followed_events,
            'recommended_events': interest_events,
            'upcoming_events': upcoming[:8],
            'recent_events': active_stamps.order_by('-updated_at')[:5],
        })

    return render(request, 'stamps/home.html', context)


@require_safe
def search(request):
    allowed = email_verified(request.user)
    form = StampSearchForm(request.GET or None)

    if allowed:
        stamps = _apply_filters(
            _active_queryset().filter(is_cancelled=False),
            form
        )
    else:
        stamps = []

    return render(request, 'stamps/search.html', {
        'allowed': allowed,
        'search_form': form,
        'stamps': stamps
    })
