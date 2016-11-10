import datetime
import json
from enum import Enum

from channels import Channel
from channels.generic.websockets import WebsocketDemultiplexer
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString
from django.utils.timezone import UTC


class DefaultManager(models.Manager):
    def default(self):
        return self.get_or_create(ident='CZYZ', defaults={'name': 'Toronto Centre'})[0]


class Facility(models.Model):
    name = models.CharField(max_length=200)
    ident = models.CharField(max_length=5, unique=True)
    location = models.PointField(null=True, blank=True)
    responsibility = models.MultiPolygonField(null=True, blank=True)

    objects = DefaultManager()

    class Meta:
        verbose_name_plural = 'facilities'

    def __str__(self):
        return self.ident

    def geojson(self):
        if self.location:
            geojson = json.loads(self.location.json)
            geojson.update({
                'id': self.ident,
                'properties': {
                    'name': self.name,
                    'responsibility': json.loads(self.responsibility.json) if self.responsibility else None,
                }
            })
            return geojson
        else:
            return ''

    @staticmethod
    def send_for_geometry(channel, geometry):
        for f in Facility.objects.filter(location__intersects=geometry):
            channel.send(WebsocketDemultiplexer.encode('facility.info', f.geojson()))


class FlightStatus(Enum):
    FILED = 'filed'
    ACTIVE = 'active'
    CLOSED = 'closed'


class Flight(models.Model):
    ident = models.CharField(max_length=20, unique=True)

    # Plan
    flight_path = models.LineStringField()
    departure_facility = models.ForeignKey(Facility, related_name='departures')
    departure_time = models.DateTimeField()
    arrival_facility = models.ForeignKey(Facility, related_name='arrivals')
    arrival_time = models.DateTimeField()

    # Current Status
    status = models.CharField(max_length=20, choices=((fs.value, fs.value) for fs in FlightStatus), default=FlightStatus.FILED.value)
    time = models.DateTimeField(auto_now_add=True)
    location = models.PointField(blank=True, null=True)
    heading = models.IntegerField(blank=True, null=True)
    track = models.LineStringField(blank=True, null=True)
    remaining_path = models.LineStringField(blank=True, null=True)
    facility = models.ForeignKey(Facility, null=True, related_name='current_flights')

    # Simulation
    current_step = models.IntegerField(default=0)
    total_seconds = models.IntegerField(default=120)
    report_seconds = models.IntegerField(default=10)

    def __str__(self):
        return self.ident

    def geojson(self):
        geojson = json.loads(self.location.json)
        geojson.update({
            'id': self.ident,
            'properties': {
                'departureFacility': self.departure_facility.ident,
                'departureTime': self.departure_time.isoformat(),
                'arrivalFacility': self.arrival_facility.ident,
                'arrivalTime': self.arrival_time.isoformat(),
                'status': self.status,
                'time': self.time.isoformat(),
                'flightPath': json.loads(self.flight_path.json) if self.flight_path else None,
                'heading': self.heading,
                'track': json.loads(self.track.json) if self.track else None,
                'remaining': json.loads(self.remaining_path.json) if self.remaining_path else None,
                'facility': self.facility.ident
            }
        })
        return geojson

    def save(self, *args, **kwargs):
        if self.location:
            # Update Track
            if self.track is None:
                self.track = LineString(self.location, self.location)
            else:
                self.track = LineString(self.track.coords + (self.location.coords,))

            # Update remaining_path
            self.remaining_path = LineString(self.location, self.arrival_facility.location)

            # Calculate Responsible facility
            try:
                self.facility = Facility.objects.get(responsibility__contains=self.location)
            except Facility.DoesNotExist:
                self.facility = Facility.objects.default()
        else:
            self.location = self.departure_facility.location
            if not self.facility_id:
                self.facility = self.departure_facility
            if not self.flight_path:
                self.flight_path = LineString(self.departure_facility.location, self.arrival_facility.location)
            if not self.remaining_path:
                self.remaining_path = self.flight_path

        super(Flight, self).save(*args, **kwargs)

    @staticmethod
    def send_for_flight_path_geometry(channel, geometry):
        for f in Flight.objects.filter(flight_path__intersects=geometry):
            channel.send(WebsocketDemultiplexer.encode('flight.info', f.geojson()))

    @staticmethod
    def send_for_remaining_path_geometry(channel, geometry):
        for f in Flight.objects.filter(remaining_path__intersects=geometry):
            channel.send(WebsocketDemultiplexer.encode('flight.info', f.geojson()))

    @staticmethod
    def send_for_location_geometry(channel, geometry):
        for f in Flight.objects.filter(location__intersects=geometry):
            channel.send(WebsocketDemultiplexer.encode('flight.info', f.geojson()))


class CurrentManager(models.Manager):
    def current(self):
        now = datetime.datetime.now(tzinfo=UTC())
        return self.filter(start__lte=now, end__lte=now)


class Weather(models.Model):
    geom = models.PolygonField()

    class Meta:
        verbose_name_plural = 'weather'

    def geojson(self):
        geojson = json.loads(self.geom.json)
        geojson.update({
            'id': self.pk,
            'properties': {}
        })
        return geojson

    @staticmethod
    def send_for_geometry(channel, geometry):
        for w in Weather.objects.filter(geom__intersects=geometry):
            channel.send(WebsocketDemultiplexer.encode('weather.info', w.geojson()))


class MapSession(models.Model):
    channel = models.CharField(max_length=200, unique=True)
    zoom = models.IntegerField(blank=True, null=True)
    bounds = models.PolygonField(blank=True, null=True)

    @staticmethod
    def send_for_geometry(message, geometry):
        for ms in MapSession.objects.filter(bounds__intersects=geometry):
            Channel(ms.channel).send(message)
