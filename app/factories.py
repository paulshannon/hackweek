import datetime
import random
import string

import factory
from django.contrib.gis.geos import LineString
from django.contrib.gis.geos import Point
from django.utils.timezone import UTC
from factory.fuzzy import FuzzyText, FuzzyDateTime, FuzzyInteger

from app.gis import buffer_geometry
from .models import FlightStatus, Facility


def utc_now_offset(**kwargs):
    return datetime.datetime.now(tz=UTC()) - datetime.timedelta(**kwargs)


class FuzzyPoint(factory.fuzzy.BaseFuzzyAttribute):
    def __init__(self, min_x=-180.0, max_x=180.0, min_y=-90.0, max_y=90.0, *args, **kwargs):
        super(FuzzyPoint, self).__init__(*args, **kwargs)
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    def fuzz(self):
        return Point(random.uniform(self.min_x, self.max_x), random.uniform(self.min_y, self.max_y))


class FacilityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'app.Facility'
        django_get_or_create = ('ident',)

    name = factory.Faker('city')
    ident = FuzzyText(prefix='C', chars=string.ascii_uppercase, length=3)
    location = FuzzyPoint(min_x=-80, max_x=-70, min_y=40, max_y=50)

    @factory.post_generation
    def responsibility(self, create, extracted, **kwargs):
        if extracted:
            self.responsibility = extracted
        else:
            self.responsibility = buffer_geometry(self.location, 30)


class FlightFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'app.Flight'
        django_get_or_create = ('ident',)

    ident = FuzzyText(prefix='C', chars=string.ascii_uppercase, length=4)
    flight_path = factory.LazyAttribute(lambda obj: LineString(obj.departure_facility.location, obj.arrival_facility.location))
    departure_facility = factory.Iterator(Facility.objects.all())
    departure_time = FuzzyDateTime(utc_now_offset(hours=3))
    arrival_facility = factory.Iterator(Facility.objects.reverse())  # Get a different iterator than departure_facility
    arrival_time = factory.LazyAttribute(lambda obj: obj.departure_time + datetime.timedelta(minutes=random.randint(30, 90)))

    status = FlightStatus.FILED.value
    time = FuzzyDateTime(utc_now_offset())
    location = FuzzyPoint()
    heading = FuzzyInteger(0, 359)
