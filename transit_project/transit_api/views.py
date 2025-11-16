from django.shortcuts import render
from rest_framework import viewsets
from .models import *


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