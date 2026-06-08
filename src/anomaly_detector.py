# Anomaly Detection for City Bike Ride Data
# Detects suspicious patterns in bike ride records
# Implements at least 5 anomaly detection rules as per requirements

import csv
import utils
from datetime import datetime

def detect_bike_overlap(records):
    """
    The same bike is used for two rides that overlap in time.
    
    Why it matters:
    This indicates a data error - a bike cannot be in two places at once.
    
    Returns:
        dict: Dictionary with 'overlapping_bikes' list and statistics
    """
    bike_rides = {}
    
    for record in records:
        bike_id = record.get("bike_id", "")
        start_time = record.get("start_time", "")
        end_time = record.get("end_time", "")
        
        if bike_id not in bike_rides:
            bike_rides[bike_id] = []
        
        bike_rides[bike_id].append({
            "ride_id": record.get("ride_id", ""),
            "start_time": start_time,
            "end_time": end_time
        })
    
    # Check for overlaps
    overlapping_bikes = []
    
    for bike_id, rides in bike_rides.items():
        # Sort rides by start time
        rides.sort(key=lambda x: x["start_time"])
        
        # Check for overlaps between consecutive rides 
        for i in range(len(rides) - 1):
            current_end = rides[i]["end_time"]
            next_start = rides[i + 1]["start_time"]
            
            # If next ride starts before current ride ends, there's an overlap
            if next_start < current_end:
                overlapping_bikes.append({
                    "bike_id": bike_id,
                    "ride1_id": rides[i]["ride_id"],
                    "ride2_id": rides[i + 1]["ride_id"],
                    "ride1_end_time": current_end,
                    "ride2_start_time": next_start,
                    "overlap_minutes": (datetime.strptime(next_start, utils.DATETIME_FMT) - datetime.strptime(current_end, utils.DATETIME_FMT)).total_seconds() / 60
                })
    
    return {
        "overlapping_bikes": overlapping_bikes,
        "total_bikes_with_overlap": len(overlapping_bikes),
        "total_rides_checked": sum(len(rides) for rides in bike_rides.values())
    }


def detect_station_spike(records):
    """
    A station has much higher usage than most stations.
    Flags stations with more than 3 times the average usage.
    
    Why it matters:
    This could indicate a real event (concert, sports match) or a data problem.
    
    Returns:
        dict: Dictionary with 'spiked_stations' list and statistics
    """
    start_station_counts = {}
    end_station_counts = {}
    
    for record in records:
        start_station = record.get("start_station", "")
        end_station = record.get("end_station", "")
        
        if start_station:
            start_station_counts[start_station] = start_station_counts.get(start_station, 0) + 1
        if end_station:
            end_station_counts[end_station] = end_station_counts.get(end_station, 0) + 1
    
    # Calculate average rides per station
    total_start_stations = len(start_station_counts)
    total_end_stations = len(end_station_counts)
    
    average_start_usage = sum(start_station_counts.values()) / total_start_stations if total_start_stations > 0 else 0
    average_end_usage = sum(end_station_counts.values()) / total_end_stations if total_end_stations > 0 else 0
    
    print("average_start_usage:", average_start_usage)
    print("average_end_usage:", average_end_usage)

    
    spiked_start_stations = [
        {"station": station, "count": count, "avg": average_start_usage, "ratio": count / average_start_usage if average_start_usage > 0 else 0}
        for station, count in start_station_counts.items()
        if count > average_start_usage * utils.STATION_SPIKE_THRESHOLD_MULTIPLIER
    ]
    
    spiked_end_stations = [
        {"station": station, "count": count, "avg": average_end_usage, "ratio": count / average_end_usage if average_end_usage > 0 else 0}
        for station, count in end_station_counts.items()
        if count > average_end_usage * utils.STATION_SPIKE_THRESHOLD_MULTIPLIER
    ]
    
    return {
        "spiked_start_stations": spiked_start_stations,
        "spiked_end_stations": spiked_end_stations,
        "average_start_usage": average_start_usage,
        "average_end_usage": average_end_usage,
        "total_start_stations": total_start_stations,
        "total_end_stations": total_end_stations
    }


def detect_route_spike(records):
    """
    A route appears much more often than normal.
    Counts each (start_station, end_station) pair and flags unusually high counts.
    
    Why it matters:
    This could show a popular commute route, a special event, or repeated bad records.
    
    Returns:
        dict: Dictionary with 'spiked_routes' list and statistics
    """
    route_counts = {}
    
    for record in records:
        start_station = record.get("start_station", "")
        end_station = record.get("end_station", "")
        
        # proceed only if both start and end stations are present and formats the string as "start -> end"
        if start_station and end_station:
            route = f"{start_station} -> {end_station}"
            route_counts[route] = route_counts.get(route, 0) + 1
    
    # Calculate average rides per route
    total_routes = len(route_counts)
    average_route_usage = sum(route_counts.values()) / total_routes if total_routes > 0 else 0
    
    spiked_routes = [
        {"route": route, "count": count, "avg": average_route_usage, "ratio": count / average_route_usage if average_route_usage > 0 else 0}
        for route, count in route_counts.items()
        if count > average_route_usage * utils.ROUTE_SPIKE_THRESHOLD_MULTIPLIER
    ]
    
    # Sort by count descending
    spiked_routes.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "spiked_routes": spiked_routes,
        "average_route_usage": average_route_usage,
        "total_routes": total_routes
    }


def detect_zero_duration(records):
    """
    A ride has a duration of 0 minutes.
    
    Why it matters:
    This could indicate a data entry error or a system issue.
    
    Note: It is ok if the start and end station are the same (same-station rides).
    
    Returns:
        dict: Dictionary with 'zero_duration_rides' list
    """
    zero_duration_rides = []

    for record in records:
        try:
            duration = float(record.get("duration_minutes", 1))  # default non-zero to skip safely
        except (ValueError, TypeError):
            continue

        start_station = record.get("start_station", "")
        end_station = record.get("end_station", "")

        if duration == 0 and start_station != end_station:
            zero_duration_rides.append(record)

    return {
        "zero_duration_rides": zero_duration_rides,
        "count": len(zero_duration_rides)
    }

def detect_duration_not_equal_with_timestamp(records):
    """
    The duration calculated from timestamps does not match the recorded duration, but is still within the tolerance
    otherwise it would still be "beyond repair".
    Records with this behaviour where flagged as "suspicious", now we put them in the dict 
    
    Why it matters:
    This could indicate a data entry error or a system issue.
    
    Returns:
        dict: Dictionary with 'duration_mismatch_records' list
    """
    duration_mismatch_records = []

    for record in records:
        start = record.get("start_time", "")
        end = record.get("end_time", "")
        dur = record.get("duration_minutes", "")

        if not start or not end or not dur:
            continue

        try:
            start_dt = datetime.strptime(start, utils.DATETIME_FMT)
            end_dt = datetime.strptime(end, utils.DATETIME_FMT)
            recorded = float(dur)
        except (ValueError, TypeError):
            continue

        calculated = (end_dt - start_dt).total_seconds() / 60.0
        diff = abs(recorded - calculated)

        if 0 < diff <= utils.DURATION_TIMESTAMP_TOLERANCE_MIN:
            duration_mismatch_records.append({
                "ride_id": record.get("ride_id"),
                "recorded_duration": recorded,
                "calculated_duration": round(calculated, 2),
                "diff_minutes": round(diff, 2),
                "status": record.get("status"),
            })

    return {
        "duration_mismatch_records": duration_mismatch_records,
        "count": len(duration_mismatch_records),
    }
    

def detect_strange_distance_duration(records):
    """
    Examples:
    - Ride distance is above 20 km but duration is under 5 minutes
    - Ride distance is below 0.2 km but duration is above 120 minutes
    
    Why it matters:
    The numbers may be individually valid but suspicious together.
    
    Returns:
        dict: Dictionary with 'suspicious_combinations' list
    """
    suspicious_combinations = []
    

    
    for record in records:
        try:
            distance = float(record.get("distance_km", ""))
            duration = float(record.get("duration_minutes", ""))
            
            # Check: High distance with very short duration
            if distance > utils.MAX_DISTANCE_FOR_SHORT_RIDE and duration < utils.MIN_DURATION_FOR_LONG_RIDE:
                suspicious_combinations.append({
                    "ride_id": record.get("ride_id", ""),
                    "type": "high_distance_short_duration",
                    "distance_km": distance,
                    "duration_minutes": duration,
                    "speed_kph": (distance / duration) * 60 if duration > 0 else 0
                })
            
            # Check: Very low distance with very long duration
            elif distance < utils.MIN_DISTANCE_FOR_LONG_RIDE and duration > utils.MAX_DURATION_FOR_SHORT_RIDE:
                suspicious_combinations.append({
                    "ride_id": record.get("ride_id", ""),
                    "type": "low_distance_long_duration",
                    "distance_km": distance,
                    "duration_minutes": duration,
                    "speed_kph": (distance / duration) * 60 if duration > 0 else 0
                })
                
        except (ValueError, TypeError):
            continue
    
    return {
        "suspicious_combinations": suspicious_combinations,
        "total_suspicious": len(suspicious_combinations)
    }


def detect_bikes_with_most_suspicious_records(records):
    """
    Detects bikes that have the most suspicious records.
    
    Why it matters:
    Bikes with many suspicious records may have broken sensors or bad checkout records.
    
    Returns:
        dict: Dictionary with top bikes by suspicious record count
    """
    bike_suspicious_counts = {}
    
    for record in records:
        status = record.get("status", "")
        bike_id = record.get("bike_id", "")
        
        if status in ["suspicious", "beyond_repair"] and bike_id:
            bike_suspicious_counts[bike_id] = bike_suspicious_counts.get(bike_id, 0) + 1
    
    # Sort by count descending and get top 5
    top_bikes = sorted(
        bike_suspicious_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return {
        "top_suspicious_bikes": [{"bike_id": bike, "suspicious_count": count} for bike, count in top_bikes],
        "total_bikes_with_suspicious": len(bike_suspicious_counts)
    }


def detect_stations_with_most_suspicious_records(records):
    """
    Detects stations that are involved in the most suspicious records.
    
    Why it matters:
    Stations with many suspicious records may have data collection issues.
    
    Returns:
        dict: Dictionary with top stations by suspicious record involvement
    """
    start_station_suspicious = {}
    end_station_suspicious = {}
    
    for record in records:
        status = record.get("status", "")
        start_station = record.get("start_station", "")
        end_station = record.get("end_station", "")
        
        if status in ["suspicious", "beyond_repair"]:
            if start_station:
                start_station_suspicious[start_station] = start_station_suspicious.get(start_station, 0) + 1
            if end_station:
                end_station_suspicious[end_station] = end_station_suspicious.get(end_station, 0) + 1
    
    # Sort by count descending and get top 5
    top_start_stations = sorted(
        start_station_suspicious.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    top_end_stations = sorted(
        end_station_suspicious.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return {
        "top_suspicious_start_stations": [{"station": station, "suspicious_count": count} for station, count in top_start_stations],
        "top_suspicious_end_stations": [{"station": station, "suspicious_count": count} for station, count in top_end_stations]
    }


def detect_duplicate_ride_ids(records):
    """
    The same ride_id appears more than once.
    
    Why it matters:
    Duplicate IDs can cause double-counting, incorrect reports, and confusion when investigating a ride.
    
    Returns:
        dict: Dictionary with duplicate ride IDs and their counts
    """
    ride_id_counts = {}
    ride_id_records = {}
    
    for record in records:
        ride_id = record.get("ride_id", "")
        if ride_id:
            ride_id_counts[ride_id] = ride_id_counts.get(ride_id, 0) + 1
            #ride_id_records.setdefault(ride_id, []).append(record)
            if ride_id in ride_id_records:
                ride_id_records[ride_id].append(record)
            else:
                ride_id_records[ride_id] = [record]
    
    # Find duplicates (count > 1)
    duplicates = [
        {"ride_id": ride_id, "count": count, "records": ride_id_records[ride_id]}
        for ride_id, count in ride_id_counts.items()
        if count > 1
    ]
    
    return {
        "duplicate_ride_ids": duplicates,
        "total_duplicates": len(duplicates)
    }


def detect_unknown_stations(records):
    """
    The start or end station is unknown or empty.
    
    Why it matters:
    Unknown stations can indicate data entry errors or system issues.
    
    Returns:
        dict: Dictionary with unknown station records
    """
    unknown_station_records = []
    
    for record in records:
        start_station = record.get("start_station", "").strip()
        end_station = record.get("end_station", "").strip()
        if start_station not in utils.dict_stations:
            unknown_station_records.append(start_station)
        if end_station not in utils.dict_stations:
            unknown_station_records.append(end_station)
        
    return {
        "unknown_station_records": unknown_station_records,
        "total_unknown_stations": len(unknown_station_records)
    }

def analyze_anomalies(input_file="data/bike_rides_cleaned.csv"):
    """
    Main function to run all anomaly detection rules on the cleaned dataset.
    
    Returns:
        dict: Dictionary containing all anomaly detection results
    """
    # Read the cleaned CSV file
    with open(input_file, "r", newline="") as file:
        reader = csv.DictReader(file)
        records = list(reader)

    records = list(filter(lambda record: record.get("status") != "beyond_repair", records))
    
    print(f"Analyzing {len(records)} records for anomalies...")
    
    # Run all anomaly detection rules
    results = {}
    
    print("  - Detecting bike overlaps...")
    results["bike_overlaps"] = detect_bike_overlap(records)

    print("  - Detecting station spikes...")
    results["station_spike"] = detect_station_spike(records)
    
    print("  - Detecting route spikes...")
    results["route_spike"] = detect_route_spike(records)

    print("  - Detecting zero duration rides...")
    results["zero_duration"] = detect_zero_duration(records)

    print("  - Detecting duration/timestamp mismatches...")
    results["duration_mismatch"] = detect_duration_not_equal_with_timestamp(records)
    
    print("  - Detecting strange distance/duration combinations...")
    results["strange_distance_duration"] = detect_strange_distance_duration(records)
    
    print("  - Detecting bikes with most suspicious records...")
    results["bikes_with_suspicious"] = detect_bikes_with_most_suspicious_records(records)
    
    print("  - Detecting stations with most suspicious records...")
    results["stations_with_suspicious"] = detect_stations_with_most_suspicious_records(records)
    
    print("  - Detecting duplicate ride IDs...")
    results["duplicate_ride_ids"] = detect_duplicate_ride_ids(records)

    print("  - Detecting unknown stations...")
    results["unknown_stations"] = detect_unknown_stations(records)
    
    print("Anomaly detection complete.")
    
    return results