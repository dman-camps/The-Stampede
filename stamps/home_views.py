"""Home feed and dedicated event discovery."""
from django.db.models import Count, F, Q
from django.shortcuts import render
from django.views.decorators.http import require_safe
from django.utils import timezone
from .models import Stamp, StampParticipation, UserFollow
from .forms import StampSearchForm
from .views import email_verified


def _base_queryset():
    return Stamp.objects.select_related('creator').annotate(
        participant_count=Count('stampparticipation')
    ).order_by('date', 'time', 'pk')


def _apply_filters(stamps, form):
    if form.is_valid():
        f = form.cleaned_data
        if f['q']:
            stamps = stamps.filter(Q(title__icontains=f['q']) | Q(desc__icontains=f['q']) | Q(location__icontains=f['q']))
        if f['category']: stamps = stamps.filter(category=f['category'])
        if f['date']: stamps = stamps.filter(date=f['date'])
        if f['location']: stamps = stamps.filter(location__icontains=f['location'])
        if f['max_cost'] is not None: stamps = stamps.filter(cost__lte=f['max_cost'])
        if f['available_only']: stamps = stamps.filter(participant_count__lt=F('max_participants'))
    else:
        stamps = stamps.none()
    return stamps


@require_safe
def home(request):
    allowed = email_verified(request.user)
    search_form = StampSearchForm(request.GET)
    context = {'allowed': allowed, 'stamps': [], 'search_form': search_form}
    if allowed:
        context['stamps'] = _apply_filters(_base_queryset().filter(is_cancelled=False), search_form)
        upcoming = _base_queryset().filter(date__gte=timezone.localdate(), is_cancelled=False)
        followed_ids = UserFollow.objects.filter(follower=request.user).values_list('followed_id', flat=True)
        followed_events = upcoming.filter(creator_id__in=followed_ids)[:4]
        joined_ids = StampParticipation.objects.filter(user=request.user).values_list('stamp_id', flat=True)
        past_events = Stamp.objects.filter(pk__in=joined_ids)
        past_interests = list(past_events.values_list('category', flat=True).distinct())
        past_locations = list(past_events.values_list('location', flat=True).distinct())
        from functools import reduce
        from operator import or_
        recommendation_terms = Q(category__in=past_interests) | Q(location__in=past_locations)
        keywords = set()
        for title, description in past_events.values_list('title', 'desc'):
            keywords.update(word.strip('.,!?()[]{}:;').lower() for word in (title + ' ' + description).split() if len(word.strip('.,!?()[]{}:;')) >= 5)
        keyword_query = reduce(or_, (Q(title__icontains=word) | Q(desc__icontains=word) | Q(location__icontains=word) for word in keywords), Q())
        interest_events = upcoming.filter(recommendation_terms | keyword_query).exclude(pk__in=joined_ids)[:4] if (past_interests or past_locations or keywords) else upcoming.none()
        context.update({
            'followed_events': followed_events,
            'recommended_events': interest_events,
            'upcoming_events': upcoming[:8],
            'recent_events': _base_queryset().filter(is_cancelled=False).order_by('-updated_at')[:5],
        })
    return render(request, 'stamps/home.html', context)


@require_safe
def search(request):
    allowed = email_verified(request.user)
    form = StampSearchForm(request.GET or None)
    stamps = _apply_filters(_base_queryset().filter(is_cancelled=False, date__gte=timezone.localdate()), form) if allowed else []
    return render(request, 'stamps/search.html', {'allowed': allowed, 'search_form': form, 'stamps': stamps})
