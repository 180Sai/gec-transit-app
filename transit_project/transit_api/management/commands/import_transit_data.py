import csv
import os
from datetime import datetime, time
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_time
from transit_api.models import Route, Stop, StopTime, Trip, Shape

def parse_gtfs_time(time_str):
    """Parse GTFS time which can be in 24+ hour format."""
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    
    # Handle times >= 24 hours by wrapping to next day (store only the time portion)
    if hours >= 24:
        hours = hours % 24
    
    return time(hours, minutes, seconds)

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Clear existing data (ignore if tables don't exist yet)
        self.stdout.write('Clearing existing data...')
        try:
            Route.objects.all().delete()
            Stop.objects.all().delete()
            StopTime.objects.all().delete()
            Trip.objects.all().delete()
            Shape.objects.all().delete()
        except Exception as e:
            self.stdout.write(f'Tables not yet created: {e}')
        
        # Get the base directory (5 levels up from this script to reach repo root)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        data_dir = os.path.join(base_dir, 'route-data')
        
        # Load Routes
        routes = []
        with open(os.path.join(data_dir, 'routes.csv'), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                routes.append(Route(
                    id=int(row['route_id']),
                    short_name=row['route_short_name'],
                    long_name=row['route_long_name'],
                    color=row['route_color']
                ))
        Route.objects.bulk_create(routes)

        # Load Stops
        stops = []
        with open(os.path.join(data_dir, 'stops.csv'), newline='') as csvfile:
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

        # Load StopTimes
        stoptimes = []
        with open(os.path.join(data_dir, 'stop_times.csv'), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                stoptimes.append(StopTime(
                    trip_id=int(row['trip_id']),
                    stop_sequence=int(row['stop_sequence']),
                    arrival_time=parse_gtfs_time(row['arrival_time']),
                    departure_time=parse_gtfs_time(row['departure_time']),
                    stop_id=int(row['stop_id']),
                    pick_up=bool(int(row['pickup_type'])),
                    drop_off=bool(int(row['drop_off_type'])),
                    shape_dist_traveled=float(row['shape_dist_traveled']) if row['shape_dist_traveled'] else 0,
                    timepoint=bool(int(row['timepoint']))
                ))
        StopTime.objects.bulk_create(stoptimes)

        # Load Trips
        trips = []
        with open(os.path.join(data_dir, 'trips.csv'), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    wheelchair = int(row['wheelchair_accessible']) if row.get('wheelchair_accessible', '').strip() else 0
                    bikes = int(row['bikes_allowed']) if row.get('bikes_allowed', '').strip() else 0
                    trips.append(Trip(
                        route_id=int(row['route_id']),
                        id=int(row['trip_id']),
                        trip_headsign=row['trip_headsign'],
                        direction_id=bool(int(row['direction_id'])) if row.get('direction_id', '').strip() else False,
                        shape_id=int(row['shape_id']) if row.get('shape_id', '').strip() else 0,
                        is_accessible=bool(wheelchair),
                        is_bikes=bool(bikes)
                    ))
                except (ValueError, KeyError) as e:
                    self.stdout.write(f'Error parsing trip row: {e}, row={row}')
                    continue
        Trip.objects.bulk_create(trips)

        # Load Shapes
        shapes = []
        with open(os.path.join(data_dir, 'shapes.csv'), newline='') as csvfile:
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
