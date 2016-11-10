from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def index(request):
    return render(request, "app/index.html", {})


@login_required
def flightplan(request):
    return render(request, "app/flightplan.html", {})
