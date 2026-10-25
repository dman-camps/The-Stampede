from django.shortcuts import render, redirect
from django.template.defaultfilters import title

from .forms import StampForm


# Create your views here.
def home(request):
    return render(request, "home.html")

def create(request):
    if request.method == "POST":
        form = StampForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("home")

    else:
        form = StampForm()

    return render(request, "create.html", {"form": form})