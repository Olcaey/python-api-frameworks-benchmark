"""
SQLAlchemy models that mirror Django benchmark tables.

Used by non-Django GraphQL frameworks to align DB shape with Django.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import declarative_base

DjangoBase = declarative_base()


class BenchmarkUser(DjangoBase):
    """SQLAlchemy mirror of django_project.users.BenchmarkUser."""

    __tablename__ = "benchmark_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(254), unique=True, index=True, nullable=False)
    first_name = Column(String(50), nullable=False, default="")
    last_name = Column(String(50), nullable=False, default="")
    is_active = Column(Boolean, default=True, nullable=False)
