from django.db import models
from decimal import Decimal

class Route(models.Model):
    id = models.IntegerField(primary_key=True)
    short_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=100)
    color = models.CharField(max_length=6)

	def __str__(self):
		return self.short_name or self.long_name

class Stop(models.Model):
    id = models.IntegerField(primary_key=True)
    code = models.IntegerField()
    name = models.CharField(max_length=100)
    desc = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

	def __str__(self):
		return self.name


class StopTime(models.Model):
    trip_id = models.IntegerField()
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    stop_id = models.IntegerField()
    pick_up = models.BooleanField(default=True)
    drop_off = models.BooleanField(default=True)
    shape_dist_traveled = models.DecimalField(max_digits=7, decimal_places=5)
    timepoint = models.BooleanField(default=True)

	class Meta:
        # This is the true key of a StopTime record.
		unique_together = ('trip', 'stop_sequence')
		ordering = ['stop_sequence']
	
	def __str__(self):
		return f"{self.trip.id} @ Seq {self.stop_sequence}: {self.stop.name}"


class Trip(models.Model):
    id = models.IntegerField(primary_key=True)
    route_id = models.IntegerField()
    trip_headsign = models.CharField(max_length=50)
    direction_id = models.BooleanField(default=True)
    shape_id = models.IntegerField()
    is_accessible = models.BooleanField(default=True)
    is_bikes = models.BooleanField(default=True)

	def __str__(self):
		return f"{self.route.short_name} - {self.trip_headsign}"


class Shape(models.Model):
    id = models.IntegerField(primary_key=True)
    shape_pt_lat = models.DecimalField(max_digits=8, decimal_places=5)
    shape_pt_lon = models.DecimalField(max_digits=8, decimal_places=5)
    shape_pt_sequence = models.IntegerField()
    shape_dist_traveled = models.DecimalField(max_digits=6, decimal_places=4)

	class Meta:
		unique_together = ('id', 'shape_pt_sequence')
		ordering = ['shape_pt_sequence']