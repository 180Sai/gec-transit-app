import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_time
from transit_api.models import Route, Stop, StopTimes, Trip, Shape

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Load Routes
        routes = []
        with open('route-data/routes.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                routes.append(Route(
                    id=int(row['route_id']),
                    short_name=row['route_short_name'],
                    long_name=row['route_long_name'],
                    color=row['route_color']
                ))
        Route.objects.bulk_create(routes)
        self.stdout.write("✅ Routes loaded.")

        # Load Stops
        stops = []
        with open('route-data/stop_id.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                stops.append(Stop(
                    id=int(row['stop_id']),
                    code=int(row['stop_code']),
                    name=row['stop_name'],
                    desc=row['stop_desc'],
                    latitude=float(row['stop_lat']),
                    longitude=float(row['stop_lon'])
                ))
        Stop.objects.bulk_create(stops)
        self.stdout.write("✅ Stops loaded.")

        # Load StopTimes
        stoptimes = []
        with open('route-data/stop_times.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                stoptimes.append(StopTimes(
                    trip_id=int(row['trip_id']),
                    arrival_time=parse_time(row['arrival_time']),
                    departure_time=parse_time(row['departure_time']),
                    stop_id=int(row['stop_id']),
                    pick_up=bool(int(row['pick_up_type'])),
                    drop_off=bool(int(row['drop_off_type'])),
                    shape_dist_traveled=float(row['shape_dist_traveled']),
                    timepoint=bool(int(row['timepoint']))
                ))
        StopTimes.objects.bulk_create(stoptimes)
        self.stdout.write("✅ StopTimes loaded.")

        # Load Trips
        trips = []
        with open('route-data/trips.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                trips.append(Trip(
                    route_id=int(row['route_id']),
                    id=int(row['trip_id']),
                    trip_headsign=row['trip_headsign'],
                    direction_id=bool(int(row['direction_id'])),
                    shape_id=int(row['shape_id']),
                    is_accessible=bool(int(row['wheelchair_accessible'])),
                    is_bikes=bool(int(row['bikes_allowed']))
                ))
        Trip.objects.bulk_create(trips)
        self.stdout.write("✅ Trips loaded.")

        # Load Shapes
        shapes = []
        with open('route-data/shapes.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                shapes.append(Shape(
                    id=int(row['shape_id']),
                    shape_pt_lat=float(row['shape_pt_lat']),
                    shape_pt_lon=float(row['shape_pt_lon']),
                    shape_pt_sequence=int(row['shape_pt_sequence']),
                    shape_dist_traveled=float(row['shape_dist_traveled'])
                ))
        Shape.objects.bulk_create(shapes)
