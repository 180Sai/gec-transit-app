from django.test import TestCase
from datetime import datetime, time

from transit_api.models import *

from transit_api.planning.planner import TransitPlanner
from transit_api.planning.itinerary import Itinerary, RouteLeg

# Gemini 2.5 Pro

class TransitPlannerTestCase(TestCase):
	"""
	Test suite for the TransitPlanner class.
	"""
	def setUp(self):
		"""
		This method runs before every test. It creates a mini, predictable
		GTFS network in the test database for the planner to use.
		"""
		# 1. Create two bus routes
		self.route1 = Route.objects.create(id='R1', short_name='R1', long_name='Crosstown')
		self.route2 = Route.objects.create(id='R2', short_name='R2', long_name='Uptown')

		# 2. Create four stops
		self.stop_a = Stop.objects.create(id='stop_a', name='Stop A', latitude=10.1, longitude=10.1)
		self.stop_b = Stop.objects.create(id='stop_b', name='Stop B', latitude=10.2, longitude=10.2)
		self.stop_c = Stop.objects.create(id='stop_c', name='Stop C', latitude=10.21, longitude=10.21) # Near B for transfer
		self.stop_d = Stop.objects.create(id='stop_d', name='Stop D', latitude=10.3, longitude=10.3)
		
		# 3. Create a trip for each route
		self.trip1 = Trip.objects.create(id='trip1', route=self.route1, trip_headsign='To Downtown')
		self.trip2 = Trip.objects.create(id='trip2', route=self.route2, trip_headsign='To University')
		
		# 4. Define the schedule (StopTimes) for the trips
		# Trip 1 goes from Stop A (9:00 AM) to Stop B (9:05 AM)
		StopTime.objects.create(
			trip=self.trip1, stop=self.stop_a, stop_sequence=1,
			arrival_time=time(9, 0), departure_time=time(9, 0)
		)
		StopTime.objects.create(
			trip=self.trip1, stop=self.stop_b, stop_sequence=2,
			arrival_time=time(9, 5), departure_time=time(9, 5)
		)
		
		# Trip 2 goes from Stop C (9:15 AM) to Stop D (9:20 AM)
		StopTime.objects.create(
			trip=self.trip2, stop=self.stop_c, stop_sequence=1,
			arrival_time=time(9, 15), departure_time=time(9, 15)
		)
		StopTime.objects.create(
			trip=self.trip2, stop=self.stop_d, stop_sequence=2,
			arrival_time=time(9, 20), departure_time=time(9, 20)
		)

	def test_planner_finds_valid_path_with_transfer(self):
		"""
		Tests if the planner can successfully find a route that requires
		a walking transfer between two different bus lines.
		"""
		# Define start/end points that require using our test network
		start_coords = {'latitude': '10.05', 'longitude': '10.05'} # Near Stop A
		end_coords = {'latitude': '10.35', 'longitude': '10.35'}   # Near Stop D
		
		# Set a start time before the first bus departs
		start_time = datetime(2025, 11, 16, 8, 55, 0)
		
		# --- Execute the planner ---
		planner = TransitPlanner(start_coords, end_coords, start_time)
		itineraries = planner.find_five_paths()
		
		# --- Assert the results ---
		# 1. We expect to find at least one valid path
		self.assertGreaterEqual(len(itineraries), 1)
		
		# 2. Analyze the first (and likely only) path found
		itinerary = itineraries[0]
		self.assertIsInstance(itinerary, Itinerary)
		
		# 3. Verify the structure of the path. We expect 5 legs:
		#    Walk -> Transit -> Walk (transfer) -> Transit -> Walk
		self.assertEqual(len(itinerary.legs), 5)
		
		# 4. Check the details of each leg to confirm the path is correct
		leg1, leg2, leg3, leg4, leg5 = itinerary.legs
		
		# Leg 1: Walk from origin to Stop A
		self.assertEqual(leg1.mode, 'walk')
		self.assertEqual(leg1.end_location_name, 'Stop A')
		
		# Leg 2: Transit on Route R1
		self.assertEqual(leg2.mode, 'transit')
		self.assertEqual(leg2.route_short_name, 'R1')
		self.assertEqual(leg2.start_location_name, 'Stop A')
		self.assertEqual(leg2.end_location_name, 'Stop B')
		
		# Leg 3: Walking transfer from Stop B to Stop C
		self.assertEqual(leg3.mode, 'walk')
		self.assertEqual(leg3.start_location_name, 'Stop B')
		self.assertEqual(leg3.end_location_name, 'Stop C')
		
		# Leg 4: Transit on Route R2
		self.assertEqual(leg4.mode, 'transit')
		self.assertEqual(leg4.route_short_name, 'R2')
		self.assertEqual(leg4.start_location_name, 'Stop C')
		self.assertEqual(leg4.end_location_name, 'Stop D')
		
		# Leg 5: Walk from Stop D to destination
		self.assertEqual(leg5.mode, 'walk')
		self.assertEqual(leg5.start_location_name, 'Stop D')
		self.assertEqual(leg5.end_location_name, 'Your Destination')

	def test_planner_no_path_found(self):
		"""
		Tests that the planner returns an empty list when no path is possible.
		"""
		# Define start/end points that are impossibly far from our test network
		start_coords = {'latitude': '50.0', 'longitude': '50.0'}
		end_coords = {'latitude': '51.0', 'longitude': '51.0'}
		start_time = datetime(2025, 11, 16, 9, 0, 0)
		
		# --- Execute the planner ---
		planner = TransitPlanner(start_coords, end_coords, start_time)
		itineraries = planner.find_five_paths()
		
		# --- Assert the result ---
		# The planner should find no nearby stops and return an empty list
		self.assertEqual(len(itineraries), 0)