import json
from urllib.request import urlopen

import requests
from channels import Channel
from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from app.models import Weather, Facility, Flight, MapSession, FlightStatus
from hackweek import settings


@receiver(post_save, sender=Flight)
def flight_saved(sender, **kwargs):
    flight = kwargs['instance']
    if flight.location:
        message = WebsocketDemultiplexer.encode('flight.info', flight.geojson())
        MapSession.send_for_geometry(message, flight.location)

        if settings.SEND_POSTS:
            requests.post(settings.POSITION_REPORT_POST_URL, data={'data': json.dumps(flight.geojson())})


@receiver(post_save, sender=MapSession)
def map_session_saved(sender, **kwargs):
    ms = kwargs['instance']
    channel = Channel(ms.channel)
    Facility.send_for_geometry(channel, ms.bounds)
    Flight.send_for_location_geometry(channel, ms.bounds)
    Weather.send_for_geometry(channel, ms.bounds)


@receiver(pre_delete, sender=Weather)
def weather_deleted(sender, **kwargs):
    weather = kwargs['instance']
    message = WebsocketDemultiplexer.encode('weather.info', {'id': weather.pk, 'remove': True})
    for ms in MapSession.objects.filter(bounds__intersects=weather.geom):
        Channel(ms.channel).send(message)


@receiver(post_save, sender=Weather)
def weather_saved(sender, **kwargs):
    weather = kwargs['instance']

    # Notify about weather
    message = WebsocketDemultiplexer.encode('weather.info', weather.geojson())

    for ms in MapSession.objects.filter(bounds__intersects=weather.geom):
        Channel(ms.channel).send(message)

    # Notify Flights with the weather in their path
    for f in Flight.objects.filter(remaining_path__intersects=weather.geom).exclude(status=FlightStatus.CLOSED.value):
        stream = 'aircraft.alert'
        payload = {
            'acid': f.ident,
            'responsible': f.facility.ident,
            'alert': 'Weather in flight path',
            'url': '{url}/#{zoom}/{point.y}/{point.x}'.format(url=settings.BASE_URL, zoom=6, point=f.remaining_path.interpolate_normalized(0.5))
        }
        if settings.SEND_POSTS:
            requests.post(settings.WEATHER_ALERT_POST_URL, data={'data': json.dumps(payload)})

        message = WebsocketDemultiplexer.encode(stream, payload)

        if f.status == FlightStatus.ACTIVE:
            for ms in MapSession.objects.filter(bounds__intersects=f.location):
                Channel(ms.channel).send(message)
