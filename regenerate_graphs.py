#!/usr/bin/env python3
"""Regenerate graphs from existing benchmark results."""

from pathlib import Path
from bench import BenchResult, generate_all_graphs

# Results from the last benchmark run
results = [
	# /json-1k
	BenchResult("django-bolt", "/json-1k", 39157, 0.00, 0.00, 0, 10),
	BenchResult("litestar", "/json-1k", 35398, 0.00, 0.00, 0, 10),
	BenchResult("fastapi", "/json-1k", 13726, 0.01, 0.00, 0, 10),
	BenchResult("django-ninja", "/json-1k", 3037, 0.03, 0.00, 0, 10),
	BenchResult("django-drf", "/json-1k", 1951, 0.05, 0.00, 0, 10),
	# /json-10k
	BenchResult("django-bolt", "/json-10k", 29857, 0.00, 0.00, 0, 10),
	BenchResult("litestar", "/json-10k", 27820, 0.00, 0.00, 0, 10),
	BenchResult("django-ninja", "/json-10k", 2652, 0.04, 0.00, 0, 10),
	BenchResult("fastapi", "/json-10k", 2565, 0.04, 0.00, 0, 10),
	BenchResult("django-drf", "/json-10k", 1702, 0.06, 0.00, 0, 10),
	# /db
	BenchResult("django-bolt", "/db", 5263, 0.02, 0.00, 0, 10),
	BenchResult("django-drf", "/db", 1489, 0.07, 0.00, 0, 10),
	BenchResult("fastapi", "/db", 1465, 0.07, 0.00, 0, 10),
	BenchResult("litestar", "/db", 1456, 0.07, 0.00, 0, 10),
	BenchResult("django-ninja", "/db", 982, 0.10, 0.00, 0, 10),
]

if __name__ == "__main__":
	print("Regenerating graphs...")
	graph_dir = Path("graphs")
	generate_all_graphs(results, graph_dir)
	print("Done! Graphs saved to graphs/")
