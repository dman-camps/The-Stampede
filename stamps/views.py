from allauth.account.models import EmailAddress
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import StampForm, AccountForm
from .models import Stamp, StampParticipation


#checks if the user has a verified UNO email
def email_verified(user):
    if not user.is_authenticated or not user.is_active:
        return False
    email = user.email.strip().lower()
    return email.endswith('@unomaha.edu') and EmailAddress.objects.filter(
        user=user, email__iexact=email, verified=True
    ).exists()


#renders the home page
def home(request):
    return render(request, "home.html")

#requires login and allows users to create a Stamp
@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if not email_verified(request.user):
        return HttpResponse("Verify your UNO email before creating Stamps.", status=403)

    #processes the submitted form
    if request.method == "POST":
        form = StampForm(request.POST)

        #saves the Stamp if the form is valid
        if form.is_valid():
            stamp = form.save(commit=False)
            stamp.creator = request.user
            stamp.save()
            return redirect("home")

    else:
        form = StampForm()

    return render(request, "create.html", {"form": form})

#allows verified users to join a Stamp
@login_required
@require_POST
def join_permission(request, pk):
    if not email_verified(request.user):
        return HttpResponse(
            "Verify your UNO email before joining Stamps.",
            status=403
        )

    from django.db import transaction

    #prevents conflicting changes during the join process
    with transaction.atomic():
        stamp = get_object_or_404(
            Stamp.objects.select_for_update(), pk=pk
        )

        if stamp.is_cancelled:
            return HttpResponse("This Stamp has been cancelled and cannot be joined.", status=400)

        #checks if the user already joined
        already_joined = StampParticipation.objects.filter(
            user=request.user,
            stamp=stamp
        ).exists()

        #redirects users who already joined
        if already_joined:
            return redirect("stamp_participants", pk=pk)

        #counts the current participants
        participant_count = StampParticipation.objects.filter(
            stamp=stamp
        ).count()

        #prevents users from exceeding the participant limit
        if participant_count >= stamp.max_participants:
            return HttpResponse(
                "Sorry, this Stamp is full.",
                status=400
            )

        #adds the user to Stamp
        StampParticipation.objects.create(
            user=request.user,
            stamp=stamp
        )

        #updates participant count
        stamp.num_participants = participant_count + 1
        stamp.save(update_fields=["num_participants"])

    return redirect("stamp_participants", pk=pk)

#shows participants of a Stamp
@login_required
@require_http_methods(["GET"])
def stamp_participants(request, pk):
    if not email_verified(request.user):
        return HttpResponse(
            "Verify your UNO email before viewing Stamps.",
            status=403
        )

    #finds requested Stamp
    stamp = get_object_or_404(Stamp, pk=pk)

    #gets participants in alphabetical order
    participants = User.objects.filter(
        stampparticipation__stamp=stamp
    ).order_by("username")

    #checks if current user joined
    has_joined = StampParticipation.objects.filter(
        user=request.user,
        stamp=stamp
    ).exists()

    participant_count = participants.count()
    is_full = participant_count >= stamp.max_participants

    return render(request, "participants.html", {
        "stamp": stamp,
        "participants": participants,
        "has_joined": has_joined,
        "participant_count": participant_count,
        "is_full": is_full,
    })

#allows users to leave Stamp
@login_required
@require_POST
def leave_stamp(request, pk):
    if not email_verified(request.user):
        return HttpResponse(
            "Verify your UNO email before leaving Stamps.",
            status=403
        )

    from django.db import transaction

    #locks the Stamp while participation and its stored count are updated
    with transaction.atomic():
        stamp = get_object_or_404(
            Stamp.objects.select_for_update(), pk=pk
        )

        StampParticipation.objects.filter(
            user=request.user,
            stamp=stamp
        ).delete()

        stamp.num_participants = StampParticipation.objects.filter(
            stamp=stamp
        ).count()
        stamp.save(update_fields=["num_participants"])

    return redirect("stamp_detail", pk=pk)

#shows details of a Stamp
@login_required
@require_http_methods(["GET"])
def stamp_detail(request, pk):
    if not email_verified(request.user):
        return HttpResponse(
            "Verify your UNO email before viewing Stamps.",
            status=403
        )

    #finds requested Stamp
    stamp = get_object_or_404(Stamp, pk=pk)

    participant_count = StampParticipation.objects.filter(
        stamp=stamp
    ).count()
    has_joined = StampParticipation.objects.filter(
        user=request.user,
        stamp=stamp
    ).exists()
    is_full = participant_count >= stamp.max_participants

    return render(request, "detail.html", {
                "stamp": stamp,
        "participant_count": participant_count,
        "has_joined": has_joined,
        "is_full": is_full,
    })

@login_required
@require_http_methods(["GET", "POST"])
def account(request):
    if request.method == "POST":
        form = AccountForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Account updated successfully.")
            return redirect("account")
    else:
        form = AccountForm(instance=request.user)

    owned_stamps = Stamp.objects.filter(creator=request.user).order_by("date", "time")
    attending_stamps = Stamp.objects.filter(pk__in=StampParticipation.objects.filter(user=request.user).values("stamp")).order_by("date", "time")

    return render(request, "stamps/account.html", {"form": form, "owned_stamps": owned_stamps, "attending_stamps": attending_stamps})
# Extended profile, organizer-following, event-management and reporting views.
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from .models import Report, UserProfile, UserFollow
from .forms import ProfileForm, ReportForm


def _profile_for(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@login_required
@require_http_methods(['GET', 'POST'])
def profile(request, username=None):
    target = get_object_or_404(User, username=username) if username else request.user
    profile_obj = _profile_for(target)
    created = Stamp.objects.filter(creator=target).order_by('-date', '-time')
    joined = Stamp.objects.filter(stampparticipation__user=target).order_by('-date', '-time')
    is_following = target != request.user and UserFollow.objects.filter(follower=request.user, followed=target).exists()
    return render(request, 'stamps/profile.html', {
        'profile_user': target, 'profile_obj': profile_obj, 'created_stamps': created,
        'joined_stamps': joined, 'is_following': is_following,
        'followers_count': target.followers.count(), 'following_count': target.following.count(),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def edit_profile(request):
    if not email_verified(request.user):
        return HttpResponse('Verify your UNO email before editing your profile.', status=403)
    profile_obj = _profile_for(request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile_obj, user=request.user)
        if form.is_valid():
            # Stage changes until the current verified UNO address confirms them.
            request.session['pending_profile'] = {
                'display_name': form.cleaned_data['display_name'],
                'bio': form.cleaned_data['bio'], 'interests': form.cleaned_data['interests'],
                'campus_location': form.cleaned_data['campus_location'],
                'first_name': form.cleaned_data['first_name'], 'last_name': form.cleaned_data['last_name'],
            }
            code = get_random_string(6, allowed_chars='0123456789')
            request.session['profile_change_code'] = {'code': code, 'created': timezone.now().timestamp()}
            send_mail('[The Stampede] Confirm profile changes',
                f'Your profile confirmation code is {code}. It expires in 10 minutes.',
                settings.DEFAULT_FROM_EMAIL, [request.user.email])
            messages.info(request, 'We sent a confirmation code to your verified UNO email. Your changes are not saved until you confirm.')
            return redirect('confirm_profile')
    else:
        form = ProfileForm(instance=profile_obj, user=request.user)
    return render(request, 'stamps/edit_profile.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def confirm_profile(request):
    if not email_verified(request.user):
        return HttpResponse('Verify your UNO email before confirming profile changes.', status=403)
    pending = request.session.get('pending_profile')
    challenge = request.session.get('profile_change_code')
    if not pending or not challenge:
        messages.warning(request, 'There are no profile changes waiting for confirmation.')
        return redirect('edit_profile')
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if timezone.now().timestamp() - challenge.get('created', 0) > 600:
            request.session.pop('pending_profile', None); request.session.pop('profile_change_code', None)
            messages.error(request, 'That confirmation code expired. Please submit your changes again.')
        elif code == challenge.get('code'):
            profile_obj = _profile_for(request.user)
            for key in ('display_name', 'bio', 'interests', 'campus_location'):
                setattr(profile_obj, key, pending[key])
            profile_obj.save()
            request.user.first_name = pending['first_name']; request.user.last_name = pending['last_name']
            request.user.save(update_fields=['first_name', 'last_name'])
            request.session.pop('pending_profile', None); request.session.pop('profile_change_code', None)
            messages.success(request, 'Your profile changes have been confirmed and saved.')
            return redirect('profile')
        else:
            messages.error(request, 'That code was not correct. Please try again.')
    return render(request, 'stamps/confirm_profile.html')


@login_required
@require_POST
def toggle_follow(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        messages.error(request, 'You cannot follow your own account.')
    else:
        relation, created = UserFollow.objects.get_or_create(follower=request.user, followed=target)
        if not created:
            relation.delete()
        messages.success(request, f'You are now following {target.username}.' if created else f'You unfollowed {target.username}.')
    return redirect('public_profile', username=target.username)


@login_required
@require_http_methods(['GET', 'POST'])
def edit_stamp(request, pk):
    stamp = get_object_or_404(Stamp, pk=pk, creator=request.user)
    if not email_verified(request.user): return HttpResponse('Verify your UNO email first.', status=403)
    if request.method == 'POST':
        form = StampForm(request.POST, instance=stamp)
        if form.is_valid():
            form.save(); messages.success(request, 'Your Stamp was updated.'); return redirect('stamp_detail', pk=pk)
    else: form = StampForm(instance=stamp)
    return render(request, 'create.html', {'form': form, 'editing': True})


@login_required
@require_POST
def cancel_stamp(request, pk):
    stamp = get_object_or_404(Stamp, pk=pk, creator=request.user)
    stamp.is_cancelled = not stamp.is_cancelled; stamp.save(update_fields=['is_cancelled', 'updated_at'])
    messages.success(request, 'Stamp cancelled.' if stamp.is_cancelled else 'Stamp cancellation reversed.')
    return redirect('stamp_detail', pk=pk)


@login_required
@require_POST
def delete_stamp(request, pk):
    stamp = get_object_or_404(Stamp, pk=pk, creator=request.user)
    stamp.delete(); messages.success(request, 'Stamp deleted.'); return redirect('profile')


@login_required
@require_http_methods(['GET', 'POST'])
def report_stamp(request, pk):
    stamp = get_object_or_404(Stamp, pk=pk)
    if stamp.creator_id == request.user.id:
        messages.error(request, 'You cannot report your own Stamp.'); return redirect('stamp_detail', pk=pk)
    if Report.objects.filter(stamp=stamp, reporter=request.user, status='pending').exists():
        messages.info(request, 'You have already reported this Stamp.'); return redirect('stamp_detail', pk=pk)
    form = ReportForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reason = form.cleaned_data['reason']
        details = form.cleaned_data['details']
        Report.objects.create(reporter=request.user, stamp=stamp, reason=f'{reason}: {details}'.strip())
        messages.success(request, 'Thank you. Your report has been sent to the moderation team.')
        return redirect('stamp_detail', pk=pk)
    return render(request, 'stamps/report.html', {'form': form, 'stamp': stamp})
