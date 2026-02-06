#!/usr/bin/env python3
"""
Framework Benchmark Runner

Benchmarks 8 ASGI frameworks with 3 endpoints each using bombardier:
- FastAPI
- Litestar
- Django Ninja
- Django Bolt
- Django REST Framework
- Graphene v3 (Django GraphQL + Starlette)
- Graphene v2 (Django GraphQL + Starlette)
- Strawberry (GraphQL + FastAPI)

Endpoints:
1. /json-1k  - ~1KB JSON response
2. /json-10k - ~10KB JSON response
3. /db       - 10 database reads

Best practices followed:
- Warmup requests before benchmarking
- Multiple runs for consistency
- Controlled concurrency
- Results saved to markdown
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from shared.versions import get_package_versions


@dataclass
class BenchConfig:
    """Benchmark configuration."""

    connections: int = 100  # Concurrent connections
    duration: int = 10      # Duration in seconds
    warmup_requests: int = 1000  # Warmup requests
    runs: int = 3           # Number of runs per endpoint


@dataclass
class BenchResult:
    """Single benchmark result."""

    framework: str
    endpoint: str
    rps: float
    latency_avg_ms: float
    latency_p99_ms: float
    errors: int
    duration_s: float


FRAMEWORKS = {
    "fastapi": {"port": 8001, "prefix": "", "type": "rest", "versions_path": "/versions"},
    "litestar": {"port": 8002, "prefix": "", "type": "rest", "versions_path": "/versions"},
    "django-ninja": {"port": 8003, "prefix": "/ninja", "type": "rest", "versions_path": "/ninja/versions"},
    "django-bolt": {"port": 8004, "prefix": "", "type": "rest", "versions_path": "/versions"},
    "django-drf": {"port": 8005, "prefix": "/drf", "type": "rest", "versions_path": "/drf/versions"},
    "graphene-v3": {"port": 8008, "prefix": "/graphql", "type": "graphql", "versions_path": "/versions"},
    "strawberry-fastapi": {"port": 8006, "prefix": "/graphql", "type": "graphql", "versions_path": "/versions"},
    "strawberry-django": {"port": 8009, "prefix": "/graphql", "type": "graphql", "versions_path": "/versions"},
    "graphene-v2": {"port": 8007, "prefix": "/graphql", "type": "graphql", "versions_path": "/versions"},
}

ENDPOINTS = [
    {"path": "/json-1k", "description": "~1KB JSON response", "method": "GET"},
    {"path": "/json-10k", "description": "~10KB JSON response", "method": "GET"},
    {"path": "/db", "description": "10 database reads", "method": "GET"},
    {"path": "/slow", "description": "2 second mock delay", "method": "GET"},
    {"path": "/nplus1", "description": "Batch-loaded related data", "method": "GET"},
    {"path": "/mutate", "description": "Mutation (write) test", "method": "POST"},
]

# GraphQL query mapping for endpoints
GRAPHQL_QUERIES = {
    "/json-1k": "query { json1k { id name description price category inStock tags } }",
    "/json-10k": "query { json10k { id name description price category inStock tags } }",
    "/db": "query { users { id username email firstName lastName isActive } }",
    "/slow": "query { slow { status delaySeconds } }",
    "/nplus1": "query { nplus1 { id username orders { id total itemCount } } }",
    "/mutate": "mutation { createItem(input: { name: \"bench-item\", quantity: 1 }) { id name quantity status } }",
}

REST_BODIES = {
    "/mutate": {"name": "bench-item", "quantity": 1},
}


def _normalize_dep_name(spec: str) -> str | None:
    spec = spec.split(";", 1)[0].strip()
    if not spec:
        return None
    name = re.split(r"[<=>!~ ]", spec, maxsplit=1)[0].strip()
    name = name.split("[", 1)[0].strip()
    return name or None


def load_project_dependency_names(pyproject_path: Path) -> list[str]:
    """Load direct dependency names from pyproject.toml (including optional groups)."""
    data = tomllib.loads(pyproject_path.read_text())
    project = data.get("project", {})

    specs: list[str] = []
    specs.extend(project.get("dependencies", []) or [])
    optional = project.get("optional-dependencies", {}) or {}
    for group_specs in optional.values():
        specs.extend(group_specs or [])

    names: list[str] = []
    for spec in specs:
        name = _normalize_dep_name(spec)
        if name:
            names.append(name)

    return sorted(set(names))


def fetch_framework_versions(host: str, port: int, versions_path: str) -> dict[str, object] | None:
    """Fetch version payload from a running framework server."""
    import urllib.request
    import urllib.error

    url = f"http://{host}:{port}{versions_path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def _run_bombardier_cmd(cmd: list[str], duration: int) -> dict | None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration + 30,
        )
        if result.returncode != 0:
            print(f"  ERROR: bombardier failed: {result.stderr}")
            return None

        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("  ERROR: bombardier timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"  ERROR: Failed to parse bombardier output: {e}")
        return None
    except FileNotFoundError:
        print("ERROR: bombardier not found. Install it first:")
        print("  go install github.com/codesenberg/bombardier@latest")
        sys.exit(1)


def run_bombardier_rest(
    url: str,
    connections: int,
    duration: int,
    method: str = "GET",
    body: dict | None = None,
) -> dict | None:
    """Run bombardier for REST and return parsed results."""
    cmd = [
        "bombardier",
        "-c", str(connections),
        "-d", f"{duration}s",
        "--print", "r",
        "--format", "json",
    ]

    if method.upper() != "GET":
        cmd.extend(["-m", method.upper()])

    body_file = None
    if body is not None:
        import tempfile
        query_payload = json.dumps(body)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(query_payload)
            body_file = f.name
        cmd.extend(["-H", "Content-Type: application/json", "-f", body_file])

    cmd.append(url)

    try:
        return _run_bombardier_cmd(cmd, duration)
    finally:
        if body_file:
            import os
            try:
                os.unlink(body_file)
            except OSError:
                pass


def warmup_rest(url: str, requests: int, method: str = "GET", body: dict | None = None) -> bool:
    """Send warmup requests using bombardier."""
    cmd = [
        "bombardier",
        "-c", "10",
        "-n", str(requests),
        "--print", "r",
    ]

    if method.upper() != "GET":
        cmd.extend(["-m", method.upper()])

    body_file = None
    if body is not None:
        import tempfile
        query_payload = json.dumps(body)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(query_payload)
            body_file = f.name
        cmd.extend(["-H", "Content-Type: application/json", "-f", body_file])

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    finally:
        if body_file:
            import os
            try:
                os.unlink(body_file)
            except OSError:
                pass


def check_server(host: str, port: int, prefix: str, framework_type: str = "rest") -> bool:
    """Check if server is responding."""
    import urllib.request
    import urllib.error

    if framework_type == "graphql":
        # For GraphQL, send a simple query
        url = f"http://{host}:{port}{prefix}"
        query_data = json.dumps({"query": GRAPHQL_QUERIES["/json-1k"]}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=query_data,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except (urllib.error.URLError, TimeoutError):
            return False
    else:
        # For REST, just GET the endpoint
        url = f"http://{host}:{port}{prefix}/json-1k"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.status == 200
        except (urllib.error.URLError, TimeoutError):
            return False


def run_bombardier_graphql(
    url: str,
    query: str,
    connections: int,
    duration: int,
) -> dict | None:
    """Run bombardier with GraphQL POST request."""
    # Create temporary file with GraphQL query
    import tempfile

    query_payload = json.dumps({"query": query})

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(query_payload)
        body_file = f.name

    try:
        cmd = [
            "bombardier",
            "-c", str(connections),
            "-d", f"{duration}s",
            "-m", "POST",
            "-H", "Content-Type: application/json",
            "-f", body_file,
            "--print", "r",
            "--format", "json",
            url,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration + 30,
        )

        if result.returncode != 0:
            print(f"  ERROR: bombardier failed: {result.stderr}")
            return None

        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print(f"  ERROR: bombardier timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"  ERROR: Failed to parse bombardier output: {e}")
        return None
    except FileNotFoundError:
        print("ERROR: bombardier not found. Install it first:")
        print("  go install github.com/codesenberg/bombardier@latest")
        sys.exit(1)
    finally:
        # Clean up temp file
        import os
        try:
            os.unlink(body_file)
        except:
            pass


def warmup_graphql(url: str, query: str, requests: int) -> bool:
    """Send warmup requests for GraphQL using bombardier."""
    import tempfile

    query_payload = json.dumps({"query": query})

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(query_payload)
        body_file = f.name

    try:
        cmd = [
            "bombardier",
            "-c", "10",
            "-n", str(requests),
            "-m", "POST",
            "-H", "Content-Type: application/json",
            "-f", body_file,
            "--print", "r",
            url,
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    finally:
        import os
        try:
            os.unlink(body_file)
        except:
            pass


def benchmark_framework(
    framework: str,
    host: str,
    port: int,
    prefix: str,
    config: BenchConfig,
    framework_type: str = "rest",
) -> list[BenchResult]:
    """Benchmark a single framework."""
    results = []
    base_url = f"http://{host}:{port}{prefix}"

    print(f"\n{'='*60}")
    print(f"Benchmarking: {framework.upper()}")
    print(f"Base URL: {base_url}")
    print(f"Type: {framework_type.upper()}")
    print(f"{'='*60}")

    # Check server
    if not check_server(host, port, prefix, framework_type):
        print(f"  ERROR: Server not responding at {base_url}")
        return results

    for endpoint in ENDPOINTS:
        path = endpoint["path"]
        method = endpoint["method"]
        print(f"\n  Endpoint: {path} ({method})")

        if framework_type == "graphql":
            # GraphQL: Use POST with query
            url = base_url
            query = GRAPHQL_QUERIES.get(path)
            if not query:
                print(f"    ERROR: No GraphQL query defined for {path}")
                continue

            # Warmup
            print(f"    Warming up ({config.warmup_requests} requests)...")
            if not warmup_graphql(url, query, config.warmup_requests):
                print(f"    WARNING: Warmup failed")

            # Multiple runs
            run_results = []
            for run in range(config.runs):
                print(f"    Run {run + 1}/{config.runs}...", end=" ", flush=True)

                data = run_bombardier_graphql(url, query, config.connections, config.duration)
                if data is None:
                    print("FAILED")
                    continue

                rps = data.get("result", {}).get("rps", {}).get("mean", 0)
                latency = data.get("result", {}).get("latency", {})
                latency_avg = latency.get("mean", 0) / 1_000_000  # ns to ms
                latency_p99 = latency.get("percentiles", {}).get("99", 0) / 1_000_000

                errors = 0
                for code, count in data.get("result", {}).get("statusCodeDistribution", {}).items():
                    if not code.startswith("2"):
                        errors += count

                print(f"RPS: {rps:,.0f}, Latency: {latency_avg:.2f}ms (p99: {latency_p99:.2f}ms)")

                run_results.append({
                    "rps": rps,
                    "latency_avg": latency_avg,
                    "latency_p99": latency_p99,
                    "errors": errors,
                })
        else:
            # REST: Use GET
            url = f"{base_url}{path}"
            body = REST_BODIES.get(path)

            # Warmup
            print(f"    Warming up ({config.warmup_requests} requests)...")
            if not warmup_rest(url, config.warmup_requests, method=method, body=body):
                print(f"    WARNING: Warmup failed")

            # Multiple runs
            run_results = []
            for run in range(config.runs):
                print(f"    Run {run + 1}/{config.runs}...", end=" ", flush=True)

                data = run_bombardier_rest(
                    url,
                    config.connections,
                    config.duration,
                    method=method,
                    body=body,
                )
                if data is None:
                    print("FAILED")
                    continue

                rps = data.get("result", {}).get("rps", {}).get("mean", 0)
                latency = data.get("result", {}).get("latency", {})
                latency_avg = latency.get("mean", 0) / 1_000_000  # ns to ms
                latency_p99 = latency.get("percentiles", {}).get("99", 0) / 1_000_000

                errors = 0
                for code, count in data.get("result", {}).get("statusCodeDistribution", {}).items():
                    if not code.startswith("2"):
                        errors += count

                print(f"RPS: {rps:,.0f}, Latency: {latency_avg:.2f}ms (p99: {latency_p99:.2f}ms)")

                run_results.append({
                    "rps": rps,
                    "latency_avg": latency_avg,
                    "latency_p99": latency_p99,
                    "errors": errors,
                })

        if run_results:
            # Take the best RPS run
            best = max(run_results, key=lambda x: x["rps"])
            results.append(BenchResult(
                framework=framework,
                endpoint=path,
                rps=best["rps"],
                latency_avg_ms=best["latency_avg"],
                latency_p99_ms=best["latency_p99"],
                errors=best["errors"],
                duration_s=config.duration,
            ))

    return results


def generate_markdown_report(
    results: list[BenchResult],
    config: BenchConfig,
    framework_versions: dict[str, dict[str, object]] | None = None,
    project_versions: dict[str, str] | None = None,
) -> str:
    """Generate markdown benchmark report."""
    lines = [
        "# Framework Benchmark Results",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Configuration",
        "",
        f"- Connections: {config.connections}",
        f"- Duration: {config.duration}s per endpoint",
        f"- Warmup: {config.warmup_requests} requests",
        f"- Runs: {config.runs} (best result taken)",
        "",
        "## Endpoints",
        "",
        "| Endpoint | Description |",
        "|----------|-------------|",
    ]

    for endpoint in ENDPOINTS:
        lines.append(f"| `{endpoint['path']}` | {endpoint['description']} |")

    lines.extend([
        "",
        "## Results",
        "",
    ])

    if framework_versions:
        lines.extend([
            "## Library Versions (Runtime by Framework)",
            "",
            "| Framework | Package | Version |",
            "|-----------|---------|---------|",
        ])
        for framework in sorted(framework_versions.keys()):
            payload = framework_versions[framework] or {}
            packages = dict(payload.get("packages", {}) or {})
            python_version = payload.get("python")
            if python_version:
                packages = {"python": python_version, **packages}
            if not packages:
                lines.append(f"| {framework} | - | - |")
                continue
            for package in sorted(packages.keys()):
                lines.append(f"| {framework} | {package} | {packages[package]} |")
        lines.append("")

    if project_versions:
        lines.extend([
            "## Library Versions (Project Dependencies)",
            "",
            "| Package | Version |",
            "|---------|---------|",
        ])
        for package in sorted(project_versions.keys()):
            lines.append(f"| {package} | {project_versions[package]} |")
        lines.append("")

    # Group by endpoint
    for endpoint in ENDPOINTS:
        path = endpoint["path"]
        endpoint_results = [r for r in results if r.endpoint == path]
        if not endpoint_results:
            continue

        lines.append(f"### {path}")
        lines.append("")
        lines.append("| Framework | RPS | Latency (avg) | Latency (p99) | Errors |")
        lines.append("|-----------|----:|-------------:|-------------:|-------:|")

        # Sort by RPS descending
        endpoint_results.sort(key=lambda x: x.rps, reverse=True)

        for r in endpoint_results:
            lines.append(
                f"| {r.framework} | {r.rps:,.0f} | {r.latency_avg_ms:.2f}ms | "
                f"{r.latency_p99_ms:.2f}ms | {r.errors} |"
            )

        lines.append("")

    # Summary table
    lines.append("## Summary (RPS by Endpoint)")
    lines.append("")

    header = "| Framework |"
    separator = "|-----------|"
    for endpoint in ENDPOINTS:
        header += f" {endpoint['path']} |"
        separator += "--------:|"

    lines.append(header)
    lines.append(separator)

    frameworks_in_results = list(set(r.framework for r in results))
    for framework in frameworks_in_results:
        row = f"| {framework} |"
        for endpoint in ENDPOINTS:
            r = next((x for x in results if x.framework == framework and x.endpoint == endpoint["path"]), None)
            if r:
                row += f" {r.rps:,.0f} |"
            else:
                row += " - |"
        lines.append(row)

    lines.append("")

    return "\n".join(lines)


# Mapping of endpoint URLs to descriptive display names for graphs
ENDPOINT_DISPLAY_NAMES = {
    "/json-1k": "1KB JSON Response",
    "/json-10k": "10KB JSON Response",
    "/db": "10 Database Reads",
    "/slow": "2s Mock Delay",
    "/nplus1": "N+1 (Batch Loaded)",
    "/mutate": "Mutation (Write)",
}

FRAMEWORK_VERSION_KEYS = {
    "fastapi": "fastapi",
    "litestar": "litestar",
    "django-ninja": "django-ninja",
    "django-bolt": "django-bolt",
    "django-drf": "djangorestframework",
    "graphene-v3": "graphene",
    "graphene-v2": "graphene",
    "strawberry-fastapi": "strawberry-graphql",
    "strawberry-django": "strawberry-graphql",
}


def build_framework_labels(framework_versions: dict[str, dict[str, object]] | None) -> dict[str, str]:
    """Build display labels with version info for graphs."""
    labels: dict[str, str] = {}
    if not framework_versions:
        return labels

    for framework, payload in framework_versions.items():
        packages = dict(payload.get("packages", {}) or {})
        key = FRAMEWORK_VERSION_KEYS.get(framework)
        version = packages.get(key) if key else None
        if version:
            labels[framework] = f"{framework} ({key} {version})"
        else:
            labels[framework] = framework
    return labels


def generate_graph(
    results: list[BenchResult],
    endpoint: str,
    output_path: Path,
    framework_labels: dict[str, str] | None = None,
) -> None:
    """Generate a bar chart with rounded corners for a specific endpoint."""
    # Filter results for this endpoint
    endpoint_results = [r for r in results if r.endpoint == endpoint]
    if not endpoint_results:
        return

    # Sort by RPS ascending (lowest first, like the reference image)
    endpoint_results.sort(key=lambda x: x.rps)

    frameworks = [r.framework for r in endpoint_results]
    label_map = framework_labels or {}
    framework_labels_list = [label_map.get(fw, fw) for fw in frameworks]
    rps_values = [r.rps for r in endpoint_results]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))

    # Colors - olive green like the reference image
    bar_color = "#8FBC8F"  # Dark sea green
    edge_color = "#6B8E6B"

    # Bar positions and width
    x_positions = range(len(frameworks))
    bar_width = 0.6

    # Draw rounded rectangle bars using FancyBboxPatch
    for i, (x, rps) in enumerate(zip(x_positions, rps_values)):
        # Create rounded rectangle
        fancy_box = FancyBboxPatch(
            (x - bar_width / 2, 0),  # (x, y) bottom-left corner
            bar_width,  # width
            rps,  # height
            boxstyle="round,pad=0,rounding_size=0.02",
            facecolor=bar_color,
            edgecolor=edge_color,
            linewidth=1,
            mutation_aspect=rps / bar_width * 0.01,  # Adjust rounding based on aspect
        )
        ax.add_patch(fancy_box)

        # Add value label above bar
        ax.text(
            x,
            rps + max(rps_values) * 0.02,
            f"{rps:,.0f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    # Set axis limits
    ax.set_xlim(-0.5, len(frameworks) - 0.5)
    ax.set_ylim(0, max(rps_values) * 1.15)

    # Labels and ticks
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(framework_labels_list, rotation=45, ha="right", fontsize=11)
    ax.set_ylabel("Requests per Second (RPS)", fontsize=12)

    # Title - use descriptive name from mapping
    endpoint_name = ENDPOINT_DISPLAY_NAMES.get(endpoint, endpoint.replace("/", "").replace("-", " ").title())
    ax.set_title(f"Framework Benchmark - {endpoint_name}", fontsize=14, fontweight="bold", pad=20)

    # Format y-axis with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    # Grid (only horizontal)
    ax.yaxis.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Tight layout
    plt.tight_layout()

    # Save
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()


def generate_combined_graph(
    results: list[BenchResult],
    output_path: Path,
    framework_labels: dict[str, str] | None = None,
    title: str = "Framework Benchmark - All Endpoints",
) -> None:
    """Generate a single chart with all frameworks grouped by endpoint."""
    if not results:
        return

    # Get unique frameworks and endpoints
    frameworks = sorted(set(r.framework for r in results))
    label_map = framework_labels or {}
    endpoints = list(set(r.endpoint for r in results))

    # Sort endpoints by the order defined in ENDPOINTS list
    endpoint_order = {ep["path"]: i for i, ep in enumerate(ENDPOINTS)}
    endpoints = sorted(endpoints, key=lambda e: endpoint_order.get(e, 999))

    # Sort frameworks by average RPS across all endpoints
    framework_avg_rps = {}
    for fw in frameworks:
        fw_results = [r.rps for r in results if r.framework == fw]
        framework_avg_rps[fw] = sum(fw_results) / len(fw_results) if fw_results else 0
    frameworks = sorted(frameworks, key=lambda f: framework_avg_rps[f], reverse=True)

    # Create figure
    _, ax = plt.subplots(figsize=(14, 8))

    # Colors for each framework (sorted by avg RPS: bolt, litestar, fastapi, ninja, drf)
    colors = ["#FF6B35", "#87CEEB", "#DDA0DD", "#F0E68C", "#8FBC8F"]  # Orange, Blue, Purple, Yellow, Green
    edge_colors = ["#CC5529", "#5F9EA0", "#BA55D3", "#BDB76B", "#6B8E6B"]

    # Bar settings
    n_frameworks = len(frameworks)
    n_endpoints = len(endpoints)
    bar_width = 0.8 / n_frameworks
    x_positions = range(n_endpoints)

    # Draw bars for each framework within each endpoint group
    for i, framework in enumerate(frameworks):
        offset = (i - n_frameworks / 2 + 0.5) * bar_width
        rps_values = []

        for endpoint in endpoints:
            r = next((x for x in results if x.framework == framework and x.endpoint == endpoint), None)
            rps_values.append(r.rps if r else 0)

        # Draw rounded bars
        for j, (x, rps) in enumerate(zip(x_positions, rps_values)):
            if rps > 0:
                fancy_box = FancyBboxPatch(
                    (x + offset - bar_width / 2, 0),
                    bar_width * 0.9,
                    rps,
                    boxstyle="round,pad=0,rounding_size=0.015",
                    facecolor=colors[i % len(colors)],
                    edgecolor=edge_colors[i % len(edge_colors)],
                    linewidth=1,
                    mutation_aspect=rps / bar_width * 0.005,
                )
                ax.add_patch(fancy_box)

                # Add value label above bar
                ax.text(
                    x + offset,
                    rps + max(r.rps for r in results) * 0.01,
                    f"{rps:,.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                    rotation=90,
                )

    # Set axis limits
    max_rps = max(r.rps for r in results)
    ax.set_xlim(-0.5, n_endpoints - 0.5)
    ax.set_ylim(0, max_rps * 1.25)

    # Labels and ticks - use descriptive endpoint names
    ax.set_xticks(list(x_positions))
    endpoint_labels = [ENDPOINT_DISPLAY_NAMES.get(ep, ep) for ep in endpoints]
    ax.set_xticklabels(endpoint_labels, rotation=45, ha="right", fontsize=11)
    ax.set_ylabel("Requests per Second (RPS)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

    # Format y-axis with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    # Grid
    ax.yaxis.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend - show frameworks
    legend_patches = [
        plt.Rectangle((0, 0), 1, 1, facecolor=colors[i % len(colors)], edgecolor=edge_colors[i % len(edge_colors)])
        for i in range(len(frameworks))
    ]
    legend_labels = [label_map.get(fw, fw) for fw in frameworks]
    ax.legend(legend_patches, legend_labels, loc="upper right", fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()


def generate_all_graphs(
    results: list[BenchResult],
    output_dir: Path,
    framework_labels: dict[str, str] | None = None,
) -> list[Path]:
    """Generate graphs for all endpoints."""
    output_dir.mkdir(exist_ok=True)
    generated = []

    endpoints_in_results = list(set(r.endpoint for r in results))

    # Individual graphs for each endpoint
    for endpoint in endpoints_in_results:
        filename = f"benchmark_{endpoint.replace('/', '').replace('-', '_')}.png"
        output_path = output_dir / filename
        generate_graph(results, endpoint, output_path, framework_labels=framework_labels)
        generated.append(output_path)
        print(f"  Generated: {output_path}")

    # Combined graph with all endpoints
    combined_path = output_dir / "benchmark_combined.png"
    generate_combined_graph(results, combined_path, framework_labels=framework_labels)
    generated.append(combined_path)
    print(f"  Generated: {combined_path}")

    return generated


def main():
    parser = argparse.ArgumentParser(description="Framework Benchmark Runner")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("-c", "--connections", type=int, default=100, help="Concurrent connections")
    parser.add_argument("-d", "--duration", type=int, default=10, help="Duration per endpoint (seconds)")
    parser.add_argument("-w", "--warmup", type=int, default=1000, help="Warmup requests")
    parser.add_argument("-r", "--runs", type=int, default=3, help="Runs per endpoint")
    parser.add_argument("-o", "--output", default="BENCHMARK_RESULTS.md", help="Output file")
    parser.add_argument("--frameworks", nargs="+", choices=list(FRAMEWORKS.keys()),
                        default=list(FRAMEWORKS.keys()), help="Frameworks to benchmark")
    parser.add_argument("--skip-slow", action="store_true", help="Skip the /slow endpoint")
    parser.add_argument(
        "--graphql-combined-graph",
        action="store_true",
        help="Generate benchmark_combined_graphql.png for GraphQL frameworks",
    )

    args = parser.parse_args()

    # Filter endpoints based on --skip-slow
    global ENDPOINTS
    if args.skip_slow:
        ENDPOINTS = [e for e in ENDPOINTS if e["path"] != "/slow"]

    config = BenchConfig(
        connections=args.connections,
        duration=args.duration,
        warmup_requests=args.warmup,
        runs=args.runs,
    )

    print("Framework Benchmark")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Connections: {config.connections}")
    print(f"Duration: {config.duration}s")
    print(f"Warmup: {config.warmup_requests} requests")
    print(f"Runs: {config.runs}")
    print(f"Frameworks: {', '.join(args.frameworks)}")

    project_versions: dict[str, str] | None = None
    framework_versions: dict[str, dict[str, object]] = {}
    try:
        project_deps = load_project_dependency_names(Path("pyproject.toml"))
        project_versions = get_package_versions(project_deps)
    except FileNotFoundError:
        project_versions = None

    for framework in args.frameworks:
        fw_config = FRAMEWORKS[framework]
        payload = fetch_framework_versions(args.host, fw_config["port"], fw_config["versions_path"])
        if payload:
            framework_versions[framework] = payload

    all_results = []

    for framework in args.frameworks:
        fw_config = FRAMEWORKS[framework]
        results = benchmark_framework(
            framework=framework,
            host=args.host,
            port=fw_config["port"],
            prefix=fw_config["prefix"],
            config=config,
            framework_type=fw_config["type"],
        )
        all_results.extend(results)

    if all_results:
        framework_labels = build_framework_labels(framework_versions or None)
        report = generate_markdown_report(
            all_results,
            config,
            framework_versions=framework_versions or None,
            project_versions=project_versions,
        )
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"\nResults saved to: {output_path}")
        print("\n" + report)

        # Generate graphs
        print("\nGenerating graphs...")
        graph_dir = Path("graphs")
        generate_all_graphs(all_results, graph_dir, framework_labels=framework_labels)
        if args.graphql_combined_graph:
            graphql_frameworks = {"graphene-v2", "graphene-v3", "strawberry-django"}
            graphql_results = [r for r in all_results if r.framework in graphql_frameworks]
            if graphql_results:
                graphql_path = graph_dir / "benchmark_combined_graphql.png"
                generate_combined_graph(
                    graphql_results,
                    graphql_path,
                    framework_labels=framework_labels,
                    title="GraphQL Framework Benchmark - All Endpoints",
                )
                print(f"  Generated: {graphql_path}")
        print(f"Graphs saved to: {graph_dir}/")
    else:
        print("\nNo results collected!")


if __name__ == "__main__":
    main()
