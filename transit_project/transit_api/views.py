from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import *
from .planning.planner import *
from .planning.itinerary import *
from .serializers import *

# Create your views here.

class RouteViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Route.objects.all()

class StopViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Stop.objects.all()

class TripViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Trip.objects.all()

class StopTimeViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = StopTime.objects.all()

class ShapesViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Shape.objects.all()

# Gemini 2.5 Pro

class PlanTripView(APIView):
	"""
	An API endpoint for planning a transit trip.

	Accepts a GET request with the following query parameters:
	- from_lat: Latitude of the starting point (e.g., 40.7128)
	- from_lon: Longitude of the starting point (e.g., -74.0060)
	- to_lat: Latitude of the destination (e.g., 40.7580)
	- to_lon: Longitude of the destination (e.g., -73.9855)
	"""
	def get(self, request, *args, **kwargs):
		# --- 1. Validate and Parse Input Parameters ---
		try:
			start_coords = {
				'latitude': request.query_params['from_lat'],
				'longitude': request.query_params['from_lon']
			}
			end_coords = {
				'latitude': request.query_params['to_lat'],
				'longitude': request.query_params['to_lon']
			}
			# For a production app, you might parse the start time from the request too
			start_time = datetime.now()
		except KeyError as e:
			# If a required parameter is missing
			return Response(
				{"error": f"Missing required query parameter: {e}"},
				status=status.HTTP_400_BAD_REQUEST
			)
		except (ValueError, TypeError) as e:
			# If a parameter has an invalid format (e.g., not a number)
			return Response(
				{"error": f"Invalid format for query parameter: {e}"},
				status=status.HTTP_400_BAD_REQUEST
			)

		# --- 2. Call the Business Logic (The Planner) ---
		try:
			planner = TransitPlanner(start_coords, end_coords, start_time)
			found_itineraries = planner.find_five_paths()
		except Exception as e:
			# Catch potential errors during planning (e.g., database issues)
			# In production, you would log this error.
			return Response(
				{"error": "An unexpected error occurred during trip planning."},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

		# --- 3. Serialize the Results ---
		# The `many=True` argument is crucial because we are serializing a list of itineraries.
		serializer = ItinerarySerializer(found_itineraries, many=True)

		# --- 4. Return the Final HTTP Response ---
		return Response(serializer.data, status=status.HTTP_200_OK)