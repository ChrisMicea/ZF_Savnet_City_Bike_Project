"""
analyzer.py
-----------
Produces analysis results from the cleaned CSV records.

Preconditions (enforced by validator + cleaner before this runs):
  - clean / fixed: all fields present and valid.
  - suspicious: same format guarantees, flagged for a semantic reason. Fields are still parseable.
  - beyond_repair: fields may be missing or malformed. Excluded from all analysis — never parsed here.

Because the pipeline already enforces the above, this module does no defensive parsing. 
"""

from collections import Counter
from datetime import datetime
import utils


# Internal helpers

def _usable(records: list[dict]) -> list[dict]:
    """Records the pipeline has not discarded — safe to parse."""
    return [r for r in records if r.get("status") in utils.ANALYSIS_STATUSES]


# datetime parser - returns datetime object
def _dt(record: dict, key: str) -> datetime:
    return datetime.strptime(record[key], utils.DATETIME_FMT)


def _avg(values: list) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _top(counter: Counter, n: int = 5) -> list[tuple]:
    return counter.most_common(n)


# def _spike_threshold(counter: Counter, multiplier: float = utils.SPIKE_THRESHOLD_MULTIPLIER) -> list[tuple]:
#     """Items whose count exceeds multiplier × mean of all counts."""
#     if not counter:
#         return []
#     mean = sum(counter.values()) / len(counter)
#     threshold = mean * multiplier
#     return [(k, v) for k, v in counter.items() if v > threshold]


# Individual analysis functions (each takes the full usable record list and returns a plain value)

def count_by_status(records: list[dict]) -> dict:
    total = len(records)
    counts = Counter(r.get("status", "beyond_repair") for r in records)
    invalid = counts.get("beyond_repair", 0)
    return {
        "total": total,
        "clean": counts.get("clean", 0),
        "fixed": counts.get("fixed", 0),
        "suspicious": counts.get("suspicious", 0),
        "beyond_repair": invalid,
        "excluded_percentage": round(invalid / total * 100, 1) if total else 0.0,
    }


def rides_by_user_type(usable: list[dict]) -> Counter:
    return Counter(r["user_type"] for r in usable)


def rides_by_station(usable: list[dict], key: str) -> Counter:
    return Counter(r[key] for r in usable if r.get(key))


def rides_by_route(usable: list[dict]) -> Counter:
    return Counter(
        (r["start_station"], r["end_station"])
        for r in usable
        if r.get("start_station") and r.get("end_station")
    )


def rides_by_bike(usable: list[dict]) -> Counter:
    return Counter(r["bike_id"] for r in usable if r.get("bike_id"))


def avg_duration(usable: list[dict]) -> float | None:
    return _avg([float(r["duration_minutes"]) for r in usable if r.get("duration_minutes")])


def avg_distance(usable: list[dict]) -> float | None:
    return _avg([float(r["distance_km"]) for r in usable if r.get("distance_km")])


def avg_by_user_type(usable: list[dict], field: str) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for r in usable:
        if r.get("user_type") and r.get(field):
            if r["user_type"] not in buckets:
                buckets[r["user_type"]] = []
            buckets[r["user_type"]].append(float(r[field]))
    return {user_type: round(sum(v) / len(v), 2) for user_type, v in buckets.items()}


def rides_by_day(usable: list[dict]) -> dict[str, int]:
    counts = {day: 0 for day in utils.DAY_NAMES}
    for r in usable:
        if r.get("start_time"):
            counts[utils.DAY_NAMES[_dt(r, "start_time").weekday()] ] += 1
    return counts


def rides_by_hour(usable: list[dict]) -> dict[int, int]:
    counts = {h: 0 for h in range(24)}
    for r in usable:
        if r.get("start_time"):
            counts[_dt(r, "start_time").hour] += 1
    return counts


def suspicious_by_bike(records: list[dict]) -> Counter:
    return Counter(
        r["bike_id"]
        for r in records
        if r.get("status") == "suspicious" and r.get("bike_id")
    )


def suspicious_by_station(records: list[dict]) -> Counter:
    counts: Counter = Counter()
    for r in records:
        if r.get("status") != "suspicious":
            continue
        if r.get("start_station"):
            counts[r["start_station"]] += 1
        if r.get("end_station"):
            counts[r["end_station"]] += 1
    return counts


def same_station_count(usable: list[dict]) -> int:
    return sum(
        1 for r in usable
        if r.get("start_station") and r["start_station"] == r.get("end_station")
    )


# Master function

def analyze(records: list[dict]) -> dict:
    """
    Run all analysis and return one results dict for the reporter.
    """
    usable = _usable(records)

    status_counts = count_by_status(records)
    by_user_type = rides_by_user_type(usable)
    by_start = rides_by_station(usable, "start_station")
    by_end = rides_by_station(usable, "end_station")
    by_route = rides_by_route(usable)
    by_bike = rides_by_bike(usable)
    day_counts = rides_by_day(usable)
    hour_counts = rides_by_hour(usable)
    susp_bikes = suspicious_by_bike(records)
    susp_stations = suspicious_by_station(records)

    return {
        # Dataset health
        "status_counts": status_counts,

        # Ride breakdowns
        "rides_by_user_type": by_user_type,
        "rides_by_start": by_start,
        "rides_by_end": by_end,

        # Popular items
        # most_common(1) returns a list of tuples, so we take the first element: [0] if it exists
        "most_popular_start": by_start.most_common(1)[0] if by_start else None,
        "most_popular_end": by_end.most_common(1)[0] if by_end else None,
        "most_popular_route": by_route.most_common(1)[0] if by_route else None,
        "top_5_routes": _top(by_route),
        "top_5_bikes": _top(by_bike),

        # Duration & distance
        "avg_duration": avg_duration(usable),
        "avg_distance": avg_distance(usable),
        "avg_duration_by_type": avg_by_user_type(usable, "duration_minutes"),
        "avg_distance_by_type": avg_by_user_type(usable, "distance_km"),

        # Time patterns
        "rides_by_day": day_counts,
        "rides_by_hour": hour_counts,
        "busiest_day": max(day_counts, key=day_counts.__getitem__),
        "quietest_day": min(day_counts, key=day_counts.__getitem__),
        "busiest_hour": max(hour_counts, key=hour_counts.__getitem__),

        # Anomalies
        "suspicious_bikes": susp_bikes,
        "suspicious_stations": susp_stations,
        # "station_spikes_start": _spike_threshold(by_start),
        # "station_spikes_end": _spike_threshold(by_end),
        # "route_spikes": _spike_threshold(by_route),
        "same_station_count": same_station_count(usable),
    }