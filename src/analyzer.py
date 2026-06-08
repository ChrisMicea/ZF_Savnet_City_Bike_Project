"""
analyzer.py
-----------
Produces all analysis results from a list of validated + cleaned ride records.

Contract with the rest of the system
-------------------------------------
INPUT:  a list of dicts, each dict being one row from the cleaned CSV.
        Every dict has these keys (after cleaning):
            ride_id, bike_id, user_type, start_station, end_station,
            start_time, end_time, duration_minutes, distance_km, status

        status is one of: "clean", "needs_cleaning", "suspicious", "beyond_repair"

OUTPUT: a single results dict that the reporter can format directly.
        Every value in the results dict is a plain Python type:
        int, float, str, list, or dict.
"""

from datetime import datetime
import utils


# Status helpers
USABLE_STATUSES = {"clean", "needs_cleaning", "suspicious"}
VALID_STATUSES   = {"clean", "needs_cleaning"}   # fully trustworthy records
INVALID_STATUS   = "beyond_repair"
SUSPICIOUS_STATUS = "suspicious"


def is_usable(record: dict) -> bool:
    """True for records that are not beyond_repair (can contribute to most analysis)."""
    return record.get("status") in USABLE_STATUSES


def is_valid(record: dict) -> bool:
    """True for clean or needs_cleaning records (fully trustworthy)."""
    return record.get("status") in VALID_STATUSES


def is_suspicious(record: dict) -> bool:
    return record.get("status") == SUSPICIOUS_STATUS


def is_invalid(record: dict) -> bool:
    return record.get("status") == INVALID_STATUS


# Small parsing helpers (used only inside this module)
def _parse_duration(record: dict) -> float | None:
    """Return duration_minutes as a float, or None if unparseable."""
    raw = record.get("duration_minutes", "")
    if not raw:
        return None
    try:
        return float(str(raw).replace(" ", ""))
    except ValueError:
        return None


def _parse_distance(record: dict) -> float | None:
    """Return distance_km as a float, or None if unparseable / missing."""
    raw = record.get("distance_km", "")
    if not raw:
        return None
    cleaned = str(raw).lower().replace("km", "").replace(" ", "")
    try:
        value = float(cleaned)
        return value if value >= 0 else None
    except ValueError:
        return None


def _parse_datetime(value: str) -> datetime | None:
    """Try each accepted format and return a datetime object, or None."""
    if not value:
        return None
    # Strip internal spaces that may survive cleaning, then re-insert separator
    value = value.replace(" ", "")
    value = value[:10] + " " + value[10:]
    for fmt in utils.accepted_date_formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


# Master function — the only thing main.py calls
def analyze(records: list[dict]) -> dict:
    """
    Run all analysis tasks and return a single results dict.

    The returned dict has these top-level keys:
        status_counts — from count_by_status()
        rides_by_user_type — dict[str, int]
        rides_by_start — dict[str, int]
        rides_by_end — dict[str, int]
        rides_by_route — dict[tuple, int]
        top_routes — list of top 5 (route_tuple, count)
        top_bikes — list of top 5 (bike_id, count)
        most_popular_start — str
        most_popular_end — str
        most_popular_route — tuple(str, str)
        duration_stats — dict from duration_stats()
        avg_distance — float | None
        avg_duration_by_type — dict[str, float]
        avg_distance_by_type — dict[str, float]
        day_of_week_counts — dict[str, int]
        hour_of_day_counts — dict[int, int]
        busiest_day — str
        quietest_day — str
        busiest_hour — int
        suspicious_bikes — dict[str, int]   top bikes by suspicious record count
        suspicious_stations — dict[str, int]   top stations by suspicious record count
        station_spikes_start — list of (station, count)
        station_spikes_end — list of (station, count)
        route_spikes — list of (route_tuple, count)
        same_station_rides — list of record dicts
        member_vs_casual — dict from member_vs_casual_summary()
    """

    # --- Core counts ---
    status_counts = count_by_status(records)

    # --- Ride groupings ---
    by_user_type   = rides_by_user_type(records)
    by_start       = rides_by_station(records, "start_station")
    by_end         = rides_by_station(records, "end_station")
    by_route       = rides_by_route(records)
    by_bike        = rides_by_bike(records)

    # --- Duration ---
    dur_stats       = duration_stats(records)
    avg_dur_by_type = average_duration_by_user_type(records)

    # --- Distance ---
    avg_dist        = average_distance(records)
    avg_dist_by_type= average_distance_by_user_type(records)

    # --- Time patterns ---
    day_counts  = rides_by_day_of_week(records)
    hour_counts = rides_by_hour_of_day(records)

    # --- Anomalies ---
    susp_bikes    = suspicious_records_by_bike(records)
    susp_stations = suspicious_records_by_station(records)

    spike_start = stations_with_spike(by_start)
    spike_end   = stations_with_spike(by_end)
    spike_routes= routes_with_spike(by_route)

    same_station = same_station_rides(records)

    # --- Comparison ---
    mv_c = member_vs_casual_summary(avg_dur_by_type, avg_dist_by_type, by_user_type)

    return {
        "status_counts":        status_counts,
        "rides_by_user_type":   by_user_type,
        "rides_by_start":       by_start,
        "rides_by_end":         by_end,
        "rides_by_route":       by_route,
        "top_routes":           top_n(by_route, 5),
        "top_bikes":            top_n(by_bike, 5),
        "most_popular_start":   most_popular(by_start),
        "most_popular_end":     most_popular(by_end),
        "most_popular_route":   most_popular(by_route),
        "duration_stats":       dur_stats,
        "avg_distance":         avg_dist,
        "avg_duration_by_type": avg_dur_by_type,
        "avg_distance_by_type": avg_dist_by_type,
        "day_of_week_counts":   day_counts,
        "hour_of_day_counts":   hour_counts,
        "busiest_day":          busiest_day(day_counts),
        "quietest_day":         quietest_day(day_counts),
        "busiest_hour":         busiest_hour(hour_counts),
        "suspicious_bikes":     susp_bikes,
        "suspicious_stations":  susp_stations,
        "station_spikes_start": spike_start,
        "station_spikes_end":   spike_end,
        "route_spikes":         spike_routes,
        "same_station_count":   len(same_station),
        "member_vs_casual":     mv_c,
    }


# Dataset-level counters
def count_by_status(records: list[dict]) -> dict:
    """
    Returns a dict with counts for each status category.

    Example return value:
        {
            "total": 10000,
            "clean": 7200,
            "needs_cleaning": 900,
            "suspicious": 400,
            "beyond_repair": 1500,
            "required_cleaning": 900,   # alias for needs_cleaning, clearer for the report
            "excluded_pct": 15.0        # percentage of records that are beyond_repair
        }
    """
    counts = {
        "total": len(records),
        "clean": 0,
        "needs_cleaning": 0,
        "suspicious": 0,
        "beyond_repair": 0,
    }
    for r in records:
        status = r.get("status", "beyond_repair")
        if status in counts:
            counts[status] += 1

    counts["required_cleaning"] = counts["needs_cleaning"]

    total = counts["total"]
    invalid = counts["beyond_repair"]
    counts["excluded_pct"] = round((invalid / total * 100), 1) if total > 0 else 0.0

    return counts


# Ride-level summaries (user type, stations, routes)
def rides_by_user_type(records: list[dict]) -> dict[str, int]:
    """
    Count usable rides grouped by user_type.

    Returns e.g. {"member": 5200, "casual": 2800, "tourist": 650}
    Only considers records that are not beyond_repair.
    """
    counts: dict[str, int] = {}
    for r in records:
        if not is_usable(r):
            continue
        user_type = r.get("user_type", "").strip().lower()
        if user_type:
            counts[user_type] = counts.get(user_type, 0) + 1
    return counts


def rides_by_station(records: list[dict], role: str) -> dict[str, int]:
    """
    Count usable rides grouped by station.

    role must be "start_station" or "end_station".
    Returns e.g. {"Central_Station": 812, "River_Park": 650, ...}
    """
    if role not in ("start_station", "end_station"):
        raise ValueError(f"role must be 'start_station' or 'end_station', got {role!r}")

    counts: dict[str, int] = {}
    for r in records:
        if not is_usable(r):
            continue
        station = r.get(role, "").strip()
        if station:
            counts[station] = counts.get(station, 0) + 1
    return counts


def rides_by_route(records: list[dict]) -> dict[tuple[str, str], int]:
    """
    Count usable rides grouped by (start_station, end_station) pair.

    Returns e.g. {("Central_Station", "River_Park"): 420, ...}
    """
    counts: dict[tuple[str, str], int] = {}
    for r in records:
        if not is_usable(r):
            continue
        start = r.get("start_station", "").strip()
        end   = r.get("end_station",   "").strip()
        if start and end:
            route = (start, end)
            counts[route] = counts.get(route, 0) + 1
    return counts


def top_n(count_dict: dict, n: int = 5) -> list[tuple]:
    """
    Return the top-n items from a count dict, sorted descending by count.

    Works for both string keys and tuple keys (routes).
    Returns a list of (key, count) tuples.
    """
    return sorted(count_dict.items(), key=lambda x: x[1], reverse=True)[:n]


def most_popular(count_dict: dict):
    """Return the single most popular key, or None if the dict is empty."""
    if not count_dict:
        return None
    return max(count_dict, key=lambda k: count_dict[k])


# Duration analysis
def average_duration(records: list[dict]) -> float | None:
    """
    Average duration_minutes across all usable records with a parseable duration.
    Returns None if no valid durations exist.
    """
    durations = [
        d for r in records
        if is_usable(r)
        for d in (_parse_duration(r),)
        if d is not None and d > 0
    ]
    return round(sum(durations) / len(durations), 1) if durations else None


def duration_stats(records: list[dict]) -> dict:
    """
    Returns a dict with:
        - average: float
        - above_180_count: int   (suspicious long rides)
        - above_360_count: int   (invalid long rides)
        - zero_or_negative_count: int
        - mismatch_count: int    (recorded duration differs from timestamp delta by > 5 min)
    Only considers usable records.
    """
    above_180 = 0
    above_360 = 0
    zero_or_neg = 0
    mismatches = 0
    valid_durations = []

    for r in records:
        if not is_usable(r):
            continue

        duration = _parse_duration(r)
        if duration is None:
            continue

        if duration <= 0:
            zero_or_neg += 1
            continue

        valid_durations.append(duration)

        if duration > 360:
            above_360 += 1
        elif duration > 180:
            above_180 += 1

        # Check if recorded duration matches timestamp delta
        start_dt = _parse_datetime(r.get("start_time", ""))
        end_dt   = _parse_datetime(r.get("end_time",   ""))
        if start_dt and end_dt:
            actual_minutes = (end_dt - start_dt).total_seconds() / 60
            if abs(actual_minutes - duration) > 5:
                mismatches += 1

    avg = round(sum(valid_durations) / len(valid_durations), 1) if valid_durations else None

    return {
        "average": avg,
        "above_180_count": above_180,
        "above_360_count": above_360,
        "zero_or_negative_count": zero_or_neg,
        "mismatch_count": mismatches,
    }


def average_duration_by_user_type(records: list[dict]) -> dict[str, float]:
    """
    Returns average duration per user type, e.g. {"member": 22.4, "casual": 31.7, ...}
    Only usable records with a valid duration are counted.
    """
    buckets: dict[str, list[float]] = {}
    for r in records:
        if not is_usable(r):
            continue
        user_type = r.get("user_type", "").strip().lower()
        duration  = _parse_duration(r)
        if user_type and duration is not None and duration > 0:
            buckets.setdefault(user_type, []).append(duration)

    return {
        ut: round(sum(vals) / len(vals), 1)
        for ut, vals in buckets.items()
    }


# Distance analysis
def average_distance(records: list[dict]) -> float | None:
    """
    Average distance_km across usable records that have a valid, non-negative distance.
    Returns None if no valid distances exist.
    """
    distances = [
        d for r in records
        if is_usable(r)
        for d in (_parse_distance(r),)
        if d is not None
    ]
    return round(sum(distances) / len(distances), 2) if distances else None


def average_distance_by_user_type(records: list[dict]) -> dict[str, float]:
    """
    Returns average distance per user type.
    Only usable records with a valid, non-negative distance are counted.
    """
    buckets: dict[str, list[float]] = {}
    for r in records:
        if not is_usable(r):
            continue
        user_type = r.get("user_type", "").strip().lower()
        distance  = _parse_distance(r)
        if user_type and distance is not None:
            buckets.setdefault(user_type, []).append(distance)

    return {
        ut: round(sum(vals) / len(vals), 2)
        for ut, vals in buckets.items()
    }


# Time-based patterns
_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def rides_by_day_of_week(records: list[dict]) -> dict[str, int]:
    """
    Count usable rides by the day of week their start_time falls on.

    Returns e.g. {"Monday": 1200, "Tuesday": 1050, ..., "Sunday": 900}
    Days with zero rides are still included so the report shows the full week.
    """
    counts = {day: 0 for day in _DAY_NAMES}
    for r in records:
        if not is_usable(r):
            continue
        dt = _parse_datetime(r.get("start_time", ""))
        if dt:
            day_name = _DAY_NAMES[dt.weekday()]
            counts[day_name] += 1
    return counts


def rides_by_hour_of_day(records: list[dict]) -> dict[int, int]:
    """
    Count usable rides by the hour their start_time falls in (0–23).

    Returns e.g. {0: 12, 1: 8, ..., 8: 420, 9: 380, ...}
    """
    counts = {h: 0 for h in range(24)}
    for r in records:
        if not is_usable(r):
            continue
        dt = _parse_datetime(r.get("start_time", ""))
        if dt:
            counts[dt.hour] += 1
    return counts


def busiest_day(day_counts: dict[str, int]) -> str | None:
    """Return the name of the day with the most rides, or None."""
    if not day_counts:
        return None
    return max(day_counts, key=lambda d: day_counts[d])


def quietest_day(day_counts: dict[str, int]) -> str | None:
    """Return the name of the day with the fewest rides, or None."""
    if not day_counts:
        return None
    return min(day_counts, key=lambda d: day_counts[d])


def busiest_hour(hour_counts: dict[int, int]) -> int | None:
    """Return the hour (0-23) with the most ride starts, or None."""
    if not hour_counts:
        return None
    return max(hour_counts, key=lambda h: hour_counts[h])


# Bike-level analysis
def rides_by_bike(records: list[dict]) -> dict[str, int]:
    """
    Count usable rides per bike_id.
    Returns e.g. {"BIKE-1042": 38, "BIKE-0271": 35, ...}
    """
    counts: dict[str, int] = {}
    for r in records:
        if not is_usable(r):
            continue
        bike_id = r.get("bike_id", "").strip().upper()
        if bike_id:
            counts[bike_id] = counts.get(bike_id, 0) + 1
    return counts


def suspicious_records_by_bike(records: list[dict]) -> dict[str, int]:
    """
    Count suspicious records per bike_id.
    Helps identify bikes that are consistently producing bad data.
    """
    counts: dict[str, int] = {}
    for r in records:
        if not is_suspicious(r):
            continue
        bike_id = r.get("bike_id", "").strip().upper()
        if bike_id:
            counts[bike_id] = counts.get(bike_id, 0) + 1
    return counts


def suspicious_records_by_station(records: list[dict]) -> dict[str, int]:
    """
    Count suspicious records per station (combining start and end appearances).
    Helps identify stations involved in the most data quality problems.
    """
    counts: dict[str, int] = {}
    for r in records:
        if not is_suspicious(r):
            continue
        for key in ("start_station", "end_station"):
            station = r.get(key, "").strip()
            if station:
                counts[station] = counts.get(station, 0) + 1
    return counts


# Anomaly / spike detection
def _average_count(count_dict: dict) -> float:
    """Return the arithmetic mean of values in a count dict."""
    if not count_dict:
        return 0.0
    return sum(count_dict.values()) / len(count_dict)


def stations_with_spike(station_counts: dict[str, int], multiplier: float = 3.0) -> list[tuple[str, int]]:
    """
    Return stations whose ride count exceeds (multiplier × average).

    Default multiplier is 3.0, matching the requirements spec.
    Returns a list of (station_name, count) tuples sorted descending.

    Why this matters: a spike could be a real event (concert, match)
    or a data problem (station logs duplicated).
    """
    avg = _average_count(station_counts)
    threshold = avg * multiplier
    spikes = [
        (station, count)
        for station, count in station_counts.items()
        if count > threshold
    ]
    return sorted(spikes, key=lambda x: x[1], reverse=True)


def routes_with_spike(route_counts: dict[tuple[str, str], int], multiplier: float = 3.0) -> list[tuple[tuple[str, str], int]]:
    """
    Return routes whose ride count exceeds (multiplier × average).

    Returns a list of ((start, end), count) tuples sorted descending.
    """
    avg = _average_count(route_counts)
    threshold = avg * multiplier
    spikes = [
        (route, count)
        for route, count in route_counts.items()
        if count > threshold
    ]
    return sorted(spikes, key=lambda x: x[1], reverse=True)


# Same-station rides
def same_station_rides(records: list[dict]) -> list[dict]:
    """
    Return all usable records where start_station == end_station.

    These may be valid (short loops) but are worth flagging for the analyst,
    especially if the duration is long.
    """
    result = []
    for r in records:
        if not is_usable(r):
            continue
        start = r.get("start_station", "").strip()
        end   = r.get("end_station",   "").strip()
        if start and end and start == end:
            result.append(r)
    return result


# Member vs casual rider comparison
def member_vs_casual_summary(duration_by_type: dict[str, float], distance_by_type: dict[str, float], rides_by_type: dict[str, int]) -> dict:
    """
    Produce a plain comparison dict between member and casual riders.

    Takes pre-computed dicts from the other functions above so there
    is no redundant iteration.

    Returns e.g.:
        {
            "member_rides": 5200,
            "casual_rides": 2800,
            "member_avg_duration": 22.4,
            "casual_avg_duration": 31.7,
            "member_avg_distance": 4.1,
            "casual_avg_distance": 3.8,
        }
    """
    return {
        "member_rides":        rides_by_type.get("member", 0),
        "casual_rides":        rides_by_type.get("casual", 0),
        "tourist_rides":       rides_by_type.get("tourist", 0),
        "member_avg_duration": duration_by_type.get("member"),
        "casual_avg_duration": duration_by_type.get("casual"),
        "tourist_avg_duration":duration_by_type.get("tourist"),
        "member_avg_distance": distance_by_type.get("member"),
        "casual_avg_distance": distance_by_type.get("casual"),
        "tourist_avg_distance":distance_by_type.get("tourist"),
    }