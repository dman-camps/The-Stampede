from allauth.account.models import EmailAddress
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.models import User
from pyexpat.errors import messages

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

    return render(request, "participants.html", {
        "stamp": stamp,
        "participants": participants,
        "has_joined": has_joined,
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

    #finds requested Stamp
    stamp = get_object_or_404(Stamp, pk=pk)

    #removes user from Stamp
    StampParticipation.objects.filter(
        user=request.user,
        stamp=stamp
    ).delete()

    #updates participant count
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

    return render(request, "detail.html", {
        "stamp": stamp
    })

@login_required
@require_http_methods(["GET", "POST"])
def account(request):
    if request.method == "POST":
        form = AccountForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("account")
    else:
        form = AccountForm(instance=request.user)

    owned_stamps = Stamp.objects.filter(creator=request.user).order_by("date", "time")
    attending_stamps = Stamp.objects.filter(pk__in=StampParticipation.objects.filter(user=request.user).values("stamp")).order_by("date", "time")

    return render(request, "stamps/account.html", {"form": form, "owned_stamps": owned_stamps, "attending_stamps": attending_stamps})