"""URL configuration for Django benchmark."""

from __future__ import annotations

from django.urls import path

from django_project.ninja_api import api
from django_project import drf_api

urlpatterns = [
    path("ninja/", api.urls),
    path("drf/json-1k", drf_api.json_1k, name="drf-json-1k"),
    path("drf/json-10k", drf_api.json_10k, name="drf-json-10k"),
    path("drf/db", drf_api.db_read, name="drf-db"),
    path("drf/slow", drf_api.slow, name="drf-slow"),
]
