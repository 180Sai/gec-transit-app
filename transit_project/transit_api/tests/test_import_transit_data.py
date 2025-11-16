import os
import csv
import tempfile
from django.core.management import call_command
from django.test import TestCase
from transit_api.models import Route, Stop, StopTime, Trip, Shape  # fixed import

class TestImportTransitData(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = os.path.join(self.temp_dir.name, 'route-data')
        os.makedirs(self.data_dir, exist_ok=True)

        self._write_csv('routes.csv', [
            ['route_id', 'route_short_name', 'route_long_name', 'route_color'],
            ['1', 'A', 'Alpha Route', 'FF0000'],
        ])

        self._write_csv('stop_id.csv', [
            ['stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon'],
            ['10', '100', 'Main St', 'Downtown stop', '43.5448', '-80.2482'],
        ])

        self._write_csv('stop_times.csv', [
            ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'pick_up_type', 'drop_off_type', 'shape_dist_traveled', 'timepoint'],
            ['1000', '08:00:00', '08:05:00', '10', '1', '0', '1.23', '1'],
        ])

        self._write_csv('trips.csv', [
            ['route_id', 'trip_id', 'trip_headsign', 'direction_id', 'shape_id', 'wheelchair_accessible', 'bikes_allowed'],
            ['1', '1000', 'To Downtown', '1', '200', '1', '0'],
        ])

        self._write_csv('shapes.csv', [
            ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence', 'shape_dist_traveled'],
            ['200', '43.5448', '-80.2482', '1', '0.0'],
        ])

        # Patch the open calls in your command to use the temp directory
        self._original_open = open
        def patched_open(path, *args, **kwargs):
            if path.startswith('route-data/'):
                path = os.path.join(self.data_dir, os.path.basename(path))
            return self._original_open(path, *args, **kwargs)
        __builtins__['open'] = patched_open

    def tearDown(self):
        self.temp_dir.cleanup()
        __builtins__['open'] = self._original_open

    def _write_csv(self, filename, rows):
        with open(os.path.join(self.data_dir, filename), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def test_import_command(self):
        call_command('import_transit_data')  # replace with your actual command name

        self.assertEqual(Route.objects.count(), 1)
        self.assertEqual(Stop.objects.count(), 1)
        self.assertEqual(StopTime.objects.count(), 1)
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(Shape.objects.count(), 1)
