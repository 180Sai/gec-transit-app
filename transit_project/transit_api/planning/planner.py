# Gemini 2.5 Pro - 2025-11-16

import heapq

from datetime import datetime, timedelta, time
from haversine import haversine, Unit
from decimal import Decimal

from django.db.models import F, Func

from transit_api.models import Stop, StopTime, Trip
from .itinerary import Itinerary, RouteLeg

# --- Constants ---
WALKING_SPEED_KPH = 5  # Kilometers per hour
MAX_WALK_METERS = 750  # Maximum distance for a transfer walk
PENALTY_AMOUNT_SECONDS = 600  # 10 minutes penalty for re-using an edge

class TransitPlanner:
	"""
	Finds multiple diverse transit routes using A* search.
	This version relies entirely on the Haversine formula for distance calculations and
	has no dependency on GeoDjango or any GIS libraries.
	"""
	def __init__(self, start_coords, end_coords, start_time):
		# Store coordinates as simple float tuples for use with haversine
		self.start_coords = (float(start_coords['latitude']), float(start_coords['longitude']))
		self.end_coords = (float(end_coords['latitude']), float(end_coords['longitude']))
		self.start_time_dt = start_time

		# Pre-fetch all stop locations into a cache to minimize DB hits.
		# This is critical for the performance of the non-GIS version.
		self.all_stops_cache = list(Stop.objects.all())
		self.stop_locations_cache = {
			stop.id: (float(stop.latitude), float(stop.longitude))
			for stop in self.all_stops_cache
		}

		# Find initial and final stops using the pure Python method
		self.nearby_start_stops = self._get_nearby_stops(self.start_coords)
		self.nearby_end_stop_ids = {s.id for s in self._get_nearby_stops(self.end_coords)}

		self.penalties = {}
		self.found_paths = []

	def find_five_paths(self):
		"""Main method to find 5 diverse paths using A* with penalization."""
		if not self.nearby_start_stops or not self.nearby_end_stop_ids:
			return []
			
		for i in range(5):
			path_result = self._a_star_search()
			if not path_result:
				break # Stop if no more paths can be found

			final_state, came_from = path_result
			itinerary = self._reconstruct_path(final_state, came_from)
			self.found_paths.append(itinerary)

			# Apply penalties to the edges of the found path for the next run
			self._apply_penalties(final_state, came_from)
		
		return self.found_paths

	def _a_star_search(self):
		"""Runs a single A* search with the current set of penalties."""
		# State: (datetime, stop_id, trip_id, stop_sequence)
		pq = []
		cost_so_far = {}
		came_from = {}

		# Initialize the search with walking from the origin to nearby stops
		for stop in self.nearby_start_stops:
			stop_coords = self.stop_locations_cache[stop.id]
			walk_seconds = self._get_walk_time_seconds(self.start_coords, stop_coords)
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

			current_stop_coords = self.stop_locations_cache.get(current_stop_id)
			if not current_stop_coords:
				continue

			# --- Generate Next Moves ---
			
			# Move 1: Stay on the current vehicle
			if on_trip_id:
				next_st = self._get_next_stop_on_trip(on_trip_id, current_seq)
				if next_st:
					cost = self._get_time_diff_seconds(current_time.time(), next_st.arrival_time)
					next_state_time = self._update_time_from_gtfs(current_time, next_st.arrival_time)
					next_state = (next_state_time, next_st.stop_id, on_trip_id, next_st.stop_sequence)
					edge = ('trip', on_trip_id, current_stop_id, next_st.stop_id)
					self._update_costs(current_state, next_state, edge, cost, came_from, cost_so_far, pq)

			# Move 2: Board a vehicle at the current stop
			departures = self._get_departures(current_stop_id, current_time)
			for st in departures:
				cost = self._get_time_diff_seconds(current_time.time(), st.departure_time)
				next_state_time = self._update_time_from_gtfs(current_time, st.departure_time)
				next_state = (next_state_time, st.stop_id, st.trip_id, st.stop_sequence)
				edge = ('board', current_stop_id, st.trip_id)
				self._update_costs(current_state, next_state, edge, cost, came_from, cost_so_far, pq)
			
			# Move 3: Walk (transfer) to another nearby stop
			for nearby_stop in self._get_nearby_stops(current_stop_coords):
				if nearby_stop.id != current_stop_id:
					nearby_stop_coords = self.stop_locations_cache[nearby_stop.id]
					cost = self._get_walk_time_seconds(current_stop_coords, nearby_stop_coords)
					next_state_time = current_time + timedelta(seconds=cost)
					next_state = (next_state_time, nearby_stop.id, None, 0)
					edge = ('walk', current_stop_id, nearby_stop.id)
					self._update_costs(current_state, next_state, edge, cost, came_from, cost_so_far, pq)
		return None

	def _update_costs(self, current_state, next_state, edge, cost, came_from, cost_so_far, pq):
		"""Helper to update costs and push to the priority queue."""
		penalty = self.penalties.get(edge, 0)
		new_cost = cost_so_far[current_state] + cost + penalty

		if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
			cost_so_far[next_state] = new_cost
			next_stop_coords = self.stop_locations_cache.get(next_state[1])
			priority = new_cost + self._heuristic(next_stop_coords)
			heapq.heappush(pq, (priority, next_state))
			came_from[next_state] = {'prev_state': current_state, 'edge': edge, 'cost': cost}

	def _get_nearby_stops(self, coords):
		"""
		Finds nearby stops by iterating through the cached list of all stops.
		This is the performance bottleneck in the non-GIS version.
		"""
		nearby = []
		for stop in self.all_stops_cache:
			stop_coords = self.stop_locations_cache[stop.id]
			if haversine(coords, stop_coords, unit=Unit.METERS) <= MAX_WALK_METERS:
				nearby.append(stop)
		return nearby

	def _get_departures(self, stop_id, dt):
		"""Finds all departures from a stop after a given time."""
		return StopTime.objects.filter(
			stop_id=stop_id,
			departure_time__gte=dt.time()
		).select_related('trip', 'trip__route').order_by('departure_time')[:5]

	def _get_next_stop_on_trip(self, trip_id, current_sequence):
		"""Finds the very next stop on a trip."""
		try:
			return StopTime.objects.select_related('stop').get(trip_id=trip_id, stop_sequence=current_sequence + 1)
		except StopTime.DoesNotExist:
			return None

	def _heuristic(self, coords):
		"""Calculates 'as the crow flies' time estimate to the destination."""
		dist_km = haversine(coords, self.end_coords, unit=Unit.KILOMETERS)
		# Assume a fast, straight-line speed of 25km/h for the heuristic
		return (dist_km / 25) * 3600

	def _get_walk_time_seconds(self, coords1, coords2):
		"""Calculates walking time between two coordinate tuples."""
		dist_km = haversine(coords1, coords2, unit=Unit.KILOMETERS)
		return (dist_km / WALKING_SPEED_KPH) * 3600

	def _get_time_diff_seconds(self, t1, t2):
		"""Calculates the difference in seconds between two time objects."""
		dummy_date = datetime(2000, 1, 1)
		return (datetime.combine(dummy_date, t2) - datetime.combine(dummy_date, t1)).total_seconds()
	
	def _update_time_from_gtfs(self, current_dt, gtfs_time):
		"""Updates a datetime object with a new time from a GTFS time object."""
		return current_dt.replace(hour=gtfs_time.hour, minute=gtfs_time.minute, second=gtfs_time.second)
	
	def _reconstruct_path(self, final_state, came_from):
		"""
		Converts the raw A* path from the 'came_from' dictionary into a clean,
		user-friendly Itinerary object with RouteLegs.
		"""
		raw_edges = []
		curr = final_state
		while curr != 'start':
			info = came_from[curr]
			raw_edges.append(info)
			curr = info['prev_state']
		raw_edges.reverse()

		legs = []
		current_transit_leg_edges = []

		for edge_info in raw_edges:
			edge = edge_info['edge']
			edge_type = edge[0]
			start_time = edge_info['prev_state'][0] if edge_info['prev_state'] != 'start' else self.start_time_dt
			end_time = start_time + timedelta(seconds=edge_info['cost'])

			if 'walk' in edge_type:
				if current_transit_leg_edges:
					legs.append(self._create_transit_leg(current_transit_leg_edges))
					current_transit_leg_edges = []

				start_name = "Your Location" if edge[1] == 'origin' else Stop.objects.get(id=edge[1]).name
				end_name = Stop.objects.get(id=edge[2]).name
				legs.append(RouteLeg(mode='walk', start_time=start_time, end_time=end_time, start_location_name=start_name, end_location_name=end_name))
			
			elif 'board' in edge_type or 'trip' in edge_type:
				current_transit_leg_edges.append(edge_info)
		
		if current_transit_leg_edges:
			legs.append(self._create_transit_leg(current_transit_leg_edges))

		last_stop_id = final_state[1]
		last_stop_obj = Stop.objects.get(id=last_stop_id)
		walk_seconds = self._get_walk_time_seconds(self.stop_locations_cache[last_stop_id], self.end_coords)
		legs.append(RouteLeg(mode='walk', start_time=final_state[0], end_time=final_state[0] + timedelta(seconds=walk_seconds), start_location_name=last_stop_obj.name, end_location_name="Your Destination"))

		return Itinerary(legs=legs)

	def _create_transit_leg(self, edges: list) -> RouteLeg:
		"""Helper to merge a sequence of trip edges into a single RouteLeg."""
		first_edge_info = edges[0]
		last_edge_info = edges[-1]

		if first_edge_info['edge'][0] == 'board':
			trip_id = first_edge_info['edge'][2]
			start_stop_id = first_edge_info['edge'][1]
		else:
			trip_id = first_edge_info['edge'][1]
			start_stop_id = first_edge_info['edge'][2]

		trip_obj = Trip.objects.select_related('route').get(id=trip_id)
		end_stop_id = last_edge_info['edge'][3]

		start_stop_name = Stop.objects.get(id=start_stop_id).name
		end_stop_name = Stop.objects.get(id=end_stop_id).name

		start_time = first_edge_info['prev_state'][0] if first_edge_info['prev_state'] != 'start' else self.start_time_dt
		end_time = last_edge_info['prev_state'][0] + timedelta(seconds=last_edge_info['cost'])

		return RouteLeg(
			mode='transit',
			start_time=start_time,
			end_time=end_time,
			start_location_name=start_stop_name,
			end_location_name=end_stop_name,
			route_short_name=trip_obj.route.short_name,
			trip_headsign=trip_obj.trip_headsign,
			num_stops=len(edges)
		)

	def _apply_penalties(self, final_state, came_from):
		"""Applies penalties to all edges in a completed path."""
		curr = final_state
		while curr != 'start':
			prev_info = came_from[curr]
			edge_id = prev_info['edge']
			self.penalties[edge_id] = self.penalties.get(edge_id, 0) + PENALTY_AMOUNT_SECONDS
			curr = prev_info['prev_state']