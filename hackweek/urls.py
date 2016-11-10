from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.views import login, logout

from app.views import index, flightplan

urlpatterns = [
    url(r'^accounts/login/$', login),
    url(r'^accounts/logout/$', logout),
    url(r'^admin/', admin.site.urls),
    url(r'^mock/flightplan/$', flightplan),
    url(r'^$', index),
]
