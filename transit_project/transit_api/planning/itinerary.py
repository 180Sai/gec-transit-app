from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

# Gemini Pro 2.5, 2025-11-16

@dataclass
class RouteLeg:
	"""Represents one segment of a journey (e.g., a single bus ride or a walk)."""	
	mode: str
	start_time: datetime
	end_time: datetime
	start_location_name: str
	end_location_name: str

	# transit-specific details
	route_short_name: Optional[str] = None
	trip_headsign: Optional[str] = None
	num_stops: Optional[int] = None

	@property
	def duration(self) -> timedelta:
		"""Calculates the duration of this leg."""
		return self.end_time - self.start_time
	
@dataclass
class Itinerary:
	"""Represents a complete journey from an origin to a destination."""
	legs: List[RouteLeg] = field(default_factory=list)

	@property
	def start_time(self) -> Optional[datetime]:
		"""The departure time of the first leg."""
		return self.legs[0].start_time if self.legs else None

	@property
	def end_time(self) -> Optional[datetime]:
		"""The arrival time of the last leg."""
		return self.legs[-1].end_time if self.legs else None
		
	@property
	def total_duration(self) -> Optional[timedelta]:
		"""The total travel time for the entire itinerary."""
		if not self.start_time or not self.end_time:
			return None
		return self.end_time - self.start_time