import csv
from datetime import datetime 
from django.core.managment.base import BaseCommand 
from django.utils.dateparse import parse_time
from transit_api.models import *

class Command(BaseCommand):
    def handle(self, *args, **options):
        obj = []
        with open('route-data/routes.csv', newline='') as csvfile:
            read = csv.DictReader(csvfile)
            for row in read:
                obj.append(
                        Route(
                            id=row['route_id'],
                            short_name=row['route_short_name'],
                            long_name=row['route_long_name'],
                            color=row['route_color']
                            )
                        )

        Route.objects.bulk_create(obj)

        obj = []
        with open('route-data/stop_id.csv', newline='') as csvfile:
            read = csv.DictReader(csvfile)
            for row in read:
                obj.append(
                        Stop(
                            id=row['stop_id'],
                            code=row['stop_code'],
                            name=row['stop_name'],
                            desc=row['stop_desc'],
                            latitude=row['stop_lat'],
                            longitude=row['stop_lon']
                            )
                        )

        Stop.objects.bulk_create(obj)

        obj = []
        with open('route-data/stop_times.csv', newline='') as csvfile:
            read = csv.DictReader(csvfile)
            for row in read:
                obj.append(
                        StopTimes(
                            trip_id=row['trip_id'],
                            arrival_time=row['arrival_time'],
                            departure_time=row['departure_time'],
                            stop_id=row['stop_id'],
                            pick_up=row['pick_up_type'],
                            drop_off=row['drop_off_type'],
                            shape_dist_traveled=row['shape_dist_traveled'],
                            timepoint=row['timepoint']
                            )
                        )

        StopTimes.objects.bulk_create(obj)


        obj = []
        with open('route-data/trips.csv', newline='') as csvfile:
            read = csv.DictReader(csvfile)
            for row in read:
                obj.append(
                        Trip(
                            route_id=row['route_id'],
                            id=row['service_id'],
                            trip_headsign=row['trip_headsign'],
                            direction_id=row['direction_id'],
                            shape_id=row['shape_id'],
                            is_accessible=row['wheelchair_accessible'],
                            is_bikes=row['bikes_allowed']
                            )
                        )

        Trip.objects.bulk_create(obj)


        obj = []
        with open('route-data/shapes.csv', newline='') as csvfile:
            read = csv.DictReader(csvfile)
            for row in read:
                obj.append(
                        Shape(
                            id=row['shape_id'],
                            shape_pt_lat=row['shape_pt_lat'],
                            shape_pt_lon=row['shape_pt_lon'],
                            shape_pt_sequence=row['shape_pt_sequence'],
                            shape_dist_traveled=row['shape_dist_traveled']
                            )
                        )

        Shape.objects.bulk_create(obj)
