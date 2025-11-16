import uuid

from django.db import models

# Create your models here.

class Route(models.Model):
	id = models.IntegerField(primary_key=True)
	short_name = models.CharField(max_length=100)
	long_name = models.CharField(max_length=100)
	color = models.CharField(max_length=6)

class Stop(models.Model):
	id = models.IntegerField(primary_key=True)
	code = models.IntegerField()
	name = models.CharField(max_length=100)
	desc = models.CharField(max_length=100)
	latitude = models.FloatField(decimal_places=6)
	longitude = models.FloatField(decimal_places=6)

class StopTime(models.Model):
	trip_id = models.IntegerField(primary_key=True)
	arrival_time = models.TimeField()
	departure_time = models.TimeField()
	stop_id = models.IntegerField()
	pick_up = models.BooleanField(default=True)
	drop_off = models.BooleanField(default=True)
	shape_dist_traveled = models.FloatField(decimal_places=5)
	timepoint = models.BooleanField(default=True)

class Trip(models.Model):
	route_id = models.IntegerField(primary_key=True)
	id = models.IntegerField()
	trip_headsign = models.CharField(max_length=50)
	direction_id = models.BooleanField(default=True)
	shape_id = models.IntegerField()
	is_accessible = models.BooleanField(default=True)
	is_bikes = models.BooleanField(default=True)

class Shape(models.Model):
	id = models.IntegerField(primary_key=True)
	shape_pt_lat = models.FloatField(decimal_places=5)
	shape_pt_lon = models.FloatField(decimal_places=5)
	shape_pt_sequence = models.IntegerField()
	shape_dist_traveled = models.FloatField(decimal_places=4)
