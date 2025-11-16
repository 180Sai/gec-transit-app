# Gemini 2.5 Pro - 2025-11-16

from rest_framework import serializers

# Note: We use serializers.Serializer because RouteLeg and Itinerary are not Django models.

class RouteLegSerializer(serializers.Serializer):
	"""
	Serializes a single RouteLeg object.
	"""
	mode = serializers.CharField()
	start_time = serializers.DateTimeField()
	end_time = serializers.DateTimeField()
	start_location_name = serializers.CharField()
	end_location_name = serializers.CharField()
	
	# --- Transit-Specific Details (can be null for walk legs) ---
	route_short_name = serializers.CharField(allow_null=True)
	trip_headsign = serializers.CharField(allow_null=True)
	num_stops = serializers.IntegerField(allow_null=True)
	
	# Use a SerializerMethodField to represent the 'duration' property
	duration_minutes = serializers.SerializerMethodField()

	def get_duration_minutes(self, obj):
		"""Returns the leg duration in whole minutes."""
		if not hasattr(obj, 'duration'):
			return None
		return round(obj.duration.total_seconds() / 60)


class ItinerarySerializer(serializers.Serializer):
	"""
	Serializes a complete Itinerary object, including its list of legs.
	"""
	# Nest the RouteLegSerializer to represent the list of legs
	legs = RouteLegSerializer(many=True, read_only=True)

	# Add top-level summary fields using SerializerMethodField
	start_time = serializers.DateTimeField()
	end_time = serializers.DateTimeField()
	total_duration_minutes = serializers.SerializerMethodField()

	def get_total_duration_minutes(self, obj):
		"""Returns the total itinerary duration in whole minutes."""
		if not hasattr(obj, 'total_duration'):
			return None
		return round(obj.total_duration.total_seconds() / 60)