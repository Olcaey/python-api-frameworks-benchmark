"""Helpers for reporting framework/package versions."""

from __future__ import annotations

import sys
from importlib import metadata


def get_package_versions(packages: list[str]) -> dict[str, str]:
    """Return a mapping of package name -> version (or 'unknown')."""
    versions: dict[str, str] = {}
    for pkg in packages:
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            versions[pkg] = "unknown"
    return versions


def build_versions_payload(framework: str, packages: list[str]) -> dict[str, object]:
    """Build a JSON-serializable payload of versions."""
    return {
        "framework": framework,
        "python": sys.version.split()[0],
        "packages": get_package_versions(packages),
    }
