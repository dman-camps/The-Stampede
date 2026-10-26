from allauth.account.models import EmailAddress
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods

from .forms import StampForm
from .models import Stamp


def email_verified(user):
    if not user.is_authenticated or not user.is_active:
        return False
    email = user.email.strip().lower()
    return email.endswith('@unomaha.edu') and EmailAddress.objects.filter(
        user=user, email__iexact=email, verified=True
    ).exists()


# Create your views here.
def home(request):
    return render(request, "home.html")

@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if not email_verified(request.user):
        return HttpResponse("Verify your UNO email before creating Stamps.", status=403)

    if request.method == "POST":
        form = StampForm(request.POST)

        if form.is_valid():
            stamp = form.save(commit=False)
            stamp.creator = request.user
            stamp.save()
            return redirect("home")

    else:
        form = StampForm()

    return render(request, "create.html", {"form": form})

@login_required
@require_POST
def join_permission(request, pk):
    if not email_verified(request.user):
        return HttpResponse("Verify your UNO email before joining Stamps.", status=403)
    get_object_or_404(Stamp, pk=pk)
    return HttpResponse("T3 permission check passed. Joining is not implemented in this contribution.")


@login_required
@require_http_methods(['GET'])
def stamp_detail(request, pk):
    if not email_verified(request.user):
        return HttpResponse('Verify your UNO email before viewing Stamps.', status=403)
    return render(request, 'detail.html', {'stamp': get_object_or_404(Stamp, pk=pk)})
