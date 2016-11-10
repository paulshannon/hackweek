import datetime
import time

from channels import Channel
from channels.generic.websockets import WebsocketDemultiplexer
from dateutil.parser import parse
from django.utils.timezone import UTC

from app.gis import compass_bearing
from app.models import Flight, FlightStatus, Facility


class Demultiplexer(WebsocketDemultiplexer):
    mapping = {
        "flightplan.state": "flightplan.state",
    }

    def connection_groups(self, *args, **kwargs):
        return ['flightplan']


def state(message):
    data = message.content
    etd = parse(data['etd'])
    total_seconds = data['total_eet']

    flight = Flight.objects.update_or_create(ident=data['acid'], defaults={
        'departure_facility': Facility.objects.get_or_create(ident=data['departure'])[0],
        'departure_time': etd,
        'arrival_facility': Facility.objects.get_or_create(ident=data['destination'])[0],
        'arrival_time': etd + datetime.timedelta(seconds=total_seconds),
        'status': data['state'],
        'total_seconds': total_seconds,
    })[0]

    if flight.status == FlightStatus.ACTIVE.value:
        Channel('flightplan.simulate').send({'pk': flight.pk})


def simulate(message):
    circle_on_arrival = True

    pk = message.content['pk']

    try:
        flight = Flight.objects.get(pk=pk)
    except Flight.DoesNotExist:
        return

    # Wait if need to wait
    td = datetime.datetime.now(tz=UTC()) - flight.time
    if td.seconds < flight.report_seconds:
        time.sleep(flight.report_seconds - td.seconds)

    # Re-grab the object
    flight = Flight.objects.get(pk=pk)
    steps = int(flight.total_seconds / flight.report_seconds)

    # Ignore flights that are closed
    if flight.status == FlightStatus.CLOSED.value:
        return

    # End of flight
    if flight.current_step == steps:
        if circle_on_arrival:
            flight.heading += 45
        else:
            flight.status = FlightStatus.CLOSED.value

    # Start a new flight
    elif flight.status == FlightStatus.FILED.value:
        flight.current_step = 0
        flight.status = FlightStatus.ACTIVE.value

    # Active flight; Move Flight
    else:
        flight.current_step += 1
        new_location = flight.flight_path.interpolate_normalized(flight.current_step / steps)
        flight.heading = compass_bearing(flight.location, new_location)
        flight.location = new_location

    flight.time = datetime.datetime.now(tz=UTC())
    flight.save()
    Channel('flightplan.simulate').send({'pk': flight.pk})
