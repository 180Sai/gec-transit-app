from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'routes', RouteViewSet)
router.register(r'stops', StopViewSet)
router.register(r'stoptimes', StopTimeViewSet)
router.register(r'trips', TripViewSet)

urlpatterns = [
	path('', include(router.urls)),
	path('plan/', PlanTripView.as_view(), name='plan-trip'),
]