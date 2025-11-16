# Gemini 2.5 Pro - 2025-11-16

import heapq

from datetime import datetime, timedelta, time
from haversine import haversine, Unit
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from django.db.models import F, Func

from transit_api.models import Stop, StopTime, Trip
from .itinerary import Itinerary, RouteLeg

# constants
WALKSPEED_KPH = 5
MAX_WALK_METERS = 500
PENALTY_AMOUNT_SECONDS = 180

class TransitPlanner:
	"""
	Finds multiple diverse transit routes using A* search with a penalization strategy.
	Uses a HYBRID GeoDjango approach for performance WITHOUT changing the models.
	"""
	def __init__(self, start_coords, end_coords, start_time):
		self.start_point = Point(float(start_coords['longitude']), float(start_coords['latitude']), srid=4326)
		self.end_point = Point(float(end_coords['longitude']), float(end_coords['latitude']), srid=4326)
		self.start_time_dt = start_time

		self.nearby_start_stops = self._get_nearby_stops(self.start_point)
		self.nearby_end_stop_ids = {s.id for s in self._get_nearby_stops(self.end_point)}
		
		# Optimization: Cache stop locations, converting Decimal to float for compatibility.
		self.stop_locations = {
			stop.id: (float(stop.latitude), float(stop.longitude)) 
			for stop in Stop.objects.all()
		}

		self.penalties = {}
		self.found_paths = []

	def find_five_paths(self):
		if not self.nearby_start_stops or not self.nearby_end_stop_ids:
			return []
			
		for i in range(5):
			path_result = self._a_star_search()
			if not path_result:
				break

			final_state, came_from = path_result
			itinerary = self._reconstruct_path(final_state, came_from)
			self.found_paths.append(itinerary)
			self._apply_penalties(final_state, came_from)
		
		return self.found_paths

	def _a_star_search(self):
		pq = []
		cost_so_far = {}
		came_from = {}

		for stop in self.nearby_start_stops:
			# Use float() on the model fields before passing to the calculation function.
			stop_coords = (float(stop.latitude), float(stop.longitude))
			walk_seconds = self._get_walk_time_seconds(self.start_point.coords, stop_coords)
			state_time = self.start_time_dt + timedelta(seconds=walk_seconds)
			state = (state_time, stop.id, None, 0)
			
			cost_so_far[state] = walk_seconds
			priority = walk_seconds + self._heuristic(stop_coords)
			heapq.heappush(pq, (priority, state))
			came_from[state] = {'prev_state': 'start', 'edge': ('walk_origin', 'origin', stop.id), 'cost': walk_seconds}

		while pq:
			priority, current_state = heapq.heappop(pq)
			current_time, current_stop_id, on_trip_id, current_seq = current_state

			if current_stop_id in self.nearby_end_stop_ids:
				return current_state, came_from

			current_stop_coords = self.stop_locations.get(current_stop_id)
			if not current_stop_coords:
				continue

			# Create a Point from the cached float coordinates for the nearby stop search
			current_stop_point = Point(current_stop_coords[1], current_stop_coords[0], srid=4326)
			for nearby_stop in self._get_nearby_stops(current_stop_point):
				if nearby_stop.id != current_stop_id:
					# Convert the nearby stop's Decimal fields to float for the calculation.
					nearby_stop_coords = (float(nearby_stop.latitude), float(nearby_stop.longitude))
					cost = self._get_walk_time_seconds(current_stop_coords, nearby_stop_coords)
					next_state_time = current_time + timedelta(seconds=cost)
					next_state = (next_state_time, nearby_stop.id, None, 0)
					edge = ('walk', current_stop_id, nearby_stop.id)
					self._update_costs(current_state, next_state, edge, cost, came_from, cost_so_far, pq)
		return None

	def _update_costs(self, current_state, next_state, edge, cost, came_from, cost_so_far, pq):
		penalty = self.penalties.get(edge, 0)
		new_cost = cost_so_far[current_state] + cost + penalty

		if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
			cost_so_far[next_state] = new_cost
			next_stop_coords = self.stop_locations.get(next_state[1])
			priority = new_cost + self._heuristic(next_stop_coords)
			heapq.heappush(pq, (priority, next_state))
			came_from[next_state] = {'prev_state': current_state, 'edge': edge, 'cost': cost}

	def _get_nearby_stops(self, point: Point):
		# ST_MakePoint function handles the numeric types from the columns correctly.
		return Stop.objects.annotate(
			location=Func(F('longitude'), F('latitude'), function='ST_MakePoint', srid=4326)
		).filter(
			location__dwithin=(point, Distance(m=MAX_WALK_METERS))
		)

	def _heuristic(self, coords):
		from haversine import haversine, Unit
		dist_km = haversine(coords, (self.end_point.y, self.end_point.x), unit=Unit.KILOMETERS)
		return (dist_km / 25) * 3600

	def _get_walk_time_seconds(self, coords1, coords2):
		from haversine import haversine, Unit
		dist_km = haversine(coords1, coords2, unit=Unit.KILOMETERS)
		return (dist_km / WALKSPEED_KPH) * 3600
		
	# --- (The rest of the file - time helpers and path reconstruction - does not use lat/lon and needs no changes) ---