from django.urls import path
from .views import get_polygons

urlpatterns = [
    path('polygons/', get_polygons),
]
