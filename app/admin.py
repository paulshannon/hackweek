from channels import Channel
from django.contrib import admin

from app.models import FlightStatus
from .models import Facility, Weather, MapSession, Flight


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    pass


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ['ident', 'status', 'current_step', 'departure_facility', 'arrival_facility']
    actions = ['simulate', 'reset']

    def simulate(self, request, queryset):
        for flight in queryset:
            Channel('flightplan.simulate').send({'pk': flight.pk})

    simulate.short_description = "Simulate Selected Flights"

    def reset(self, request, queryset):
        for flight in queryset:
            flight.status = FlightStatus.FILED.value
            flight.location = None
            flight.heading = None
            flight.current_step = 0
            flight.save()

    reset.short_description = "Reset Selected Flights"


@admin.register(Weather)
class WeatherAdmin(admin.ModelAdmin):
    pass


@admin.register(MapSession)
class MapSessionAdmin(admin.ModelAdmin):
    pass
