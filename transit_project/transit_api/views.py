from django.shortcuts import render
from rest_framework import viewsets
from .models import *

from django.http import JsonResponse
from django.views.decorators.http import require_GET

def get_nearby_stops(address):
	stops = Stop.objects.all()
	


@require_GET
def get_shortest_routes(request):
		try:
			start = {
				'lat': request.GET['start_lat'],
				'lon': request.GET['start_lon']
			}
			destination = {
				'lat': request.GET['destination_lat'],
				'lon': request.GET['destination_lon']
			}
		except KeyError as e:
			return JsonResponse({'error': f'Missing parameter: {str(e)}'}, status=400)

		routes = [
			# find shortest route
		]
		return JsonResponse({'routes': routes})


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