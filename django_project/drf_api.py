"""
Django REST Framework Benchmark API

4 endpoints:
1. GET /json-1k     - Returns ~1KB JSON response
2. GET /json-10k    - Returns ~10KB JSON response
3. GET /db          - 10 reads from SQLite database
4. GET /slow        - Mock API that takes 2 seconds to respond
"""

from __future__ import annotations

import asyncio
import sys

from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django_project.users.models import BenchmarkUser

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
import test_data


class UserSerializer(serializers.ModelSerializer):
	"""User response serializer."""

	class Meta:
		model = BenchmarkUser
		fields = ["id", "username", "email", "first_name", "last_name", "is_active"]


@api_view(["GET"])
def json_1k(request):
	"""Return ~1KB JSON response."""
	return Response(test_data.JSON_1K)


@api_view(["GET"])
def json_10k(request):
	"""Return ~10KB JSON response."""
	return Response(test_data.JSON_10K)


@api_view(["GET"])
def db_read(request):
	"""Read 10 users from database."""
	users = list(BenchmarkUser.objects.all()[:10])
	serializer = UserSerializer(users, many=True)
	return Response(serializer.data)


@api_view(["GET"])
def slow(request):
	"""Mock slow API - 2 second delay."""
	import time
	time.sleep(2)
	return Response({"status": "ok", "delay_seconds": 2})
