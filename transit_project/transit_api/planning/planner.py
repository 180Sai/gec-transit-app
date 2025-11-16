# Gemini 2.5 Pro - 2025-11-16

import heapq

from datetime import datetime, timedelta, time
from haversine import haversine, Unit
from decimal import Decimal

from django.db.models import F, Func

from transit_api.models import Stop, StopTime, Trip
from .itinerary import Itinerary, RouteLeg

# constants
WALKSPEED_KPH = 5
MAX_WALK_METERS = 500
PENALTY_AMOUNT_SECONDS = 180

class TransitPlanner:
	pass