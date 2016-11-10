from itertools import combinations

import factory
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from ...factories import FacilityFactory, FlightFactory
from ...models import Facility, Flight


class Command(BaseCommand):
    help = 'Initialize the database with fake data'

    def handle(self, *args, **options):
        Facility.objects.all().delete()
        Flight.objects.all().delete()

        factory.fuzzy.reseed_random('hackweek')

        Facility.objects.create(name='Toronto Centre', ident='CZYZ', location=None, responsibility=None)

        airports = [
            FacilityFactory(name='Ottawa Macdonald–Cartier International Airport', ident='CYOW', location=Point(-75.6692, 45.3192)),
            # FacilityFactory(name='Gatineau - Ottawa Executive Airport', ident='CYND', location=Point(-75.5615, 45.5210)),
            FacilityFactory(name='Toronto Pearson International Airport', ident='CYYZ', location=Point(-79.6248, 43.6777)),
            FacilityFactory(name='John F. Kennedy International Airport', ident='KJFK', location=Point(-73.7781, 40.6413)),
            FacilityFactory(name='Logan International Airport', ident='KBOS', location=Point(-71.0096, 42.3656)),
        ]

        for a, b in combinations(airports, 2):
            FlightFactory(departure_facility=a, arrival_facility=b, location=None)
            FlightFactory(departure_facility=b, arrival_facility=a, location=None)

        self.stdout.write(self.style.SUCCESS('init_app Success!'))
