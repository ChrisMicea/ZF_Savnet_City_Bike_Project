# Anomaly Detection for City Bike Ride Data
# Detects suspicious patterns in bike ride records
# Implements at least 5 anomaly detection rules as per requirements

import csv
import utils

def detect_bike_overlap(records):
    """
    Anomaly Rule 8: Bike Overlap
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
                    "overlap_minutes": (utils.parse_datetime(next_start) - utils.parse_datetime(current_end)).total_seconds() / 60
                })
    
    return {
        "overlapping_bikes": overlapping_bikes,
        "total_bikes_with_overlap": len(overlapping_bikes),
        "total_rides_checked": sum(len(rides) for rides in bike_rides.values())
    }

def detect_station_spike(records):
    """
    Anomaly Rule 7: Suspicious Station Spike
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

    # Flag stations with >3x average usage
    SPIKE_THRESHOLD = 3.0
    
    spiked_start_stations = [
        {"station": station, "count": count, "avg": average_start_usage, "ratio": count / average_start_usage if average_start_usage > 0 else 0}
        for station, count in start_station_counts.items()
        if count > average_start_usage * SPIKE_THRESHOLD
    ]
    
    spiked_end_stations = [
        {"station": station, "count": count, "avg": average_end_usage, "ratio": count / average_end_usage if average_end_usage > 0 else 0}
        for station, count in end_station_counts.items()
        if count > average_end_usage * SPIKE_THRESHOLD
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
    Anomaly Rule 8: Suspicious Route Spike
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
    
    # Flag routes with >3x average usage
    SPIKE_THRESHOLD = 3.0
    
    spiked_routes = [
        {"route": route, "count": count, "avg": average_route_usage, "ratio": count / average_route_usage if average_route_usage > 0 else 0}
        for route, count in route_counts.items()
        if count > average_route_usage * SPIKE_THRESHOLD
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
    Anomaly Rule 10: Zero Duration
    A ride has a duration of 0 minutes.
    
    Why it matters:
    This could indicate a data entry error or a system issue.
    
    Note: It is ok if the start and end station are the same (same-station rides).
    
    Returns:
        dict: Dictionary with 'zero_duration_rides' list
    """
    zero_duration_rides = []
    
    for record in records:
        duration = record.get("duration_minutes", 0)
        start_station = record.get("start_station", "")
        end_station = record.get("end_station", "")
        
        # Only flag as suspicious if duration is 0 AND stations are different
        if duration == 0 and start_station != end_station:
            zero_duration_rides.append(record)
    
    return {
        "zero_duration_rides": zero_duration_rides,
        "count": len(zero_duration_rides)
    }

# def detect_duration_not_equal_with_timestamp(records):
#     """
#     Anomaly Rule 11: Duration Not Equal with Timestamp
#     The duration calculated from timestamps does not match the recorded duration, but is still within the tolerance
#     otherwise it would still be "beyond repair".
#     Records with this behaviour where flagged as "suspicious", now we put them in the dict 
    
#     Why it matters:
#     This could indicate a data entry error or a system issue.
    
#     Returns:
#         dict: Dictionary with 'duration_mismatch_records' list
#     """
    

def detect_strange_distance_duration(records):
    """
    Anomaly Rule 9: Strange Distance and Duration Combination
    Examples:
    - Ride distance is above 20 km but duration is under 5 minutes
    - Ride distance is below 0.2 km but duration is above 120 minutes
    
    Why it matters:
    The numbers may be individually valid but suspicious together.
    
    Returns:
        dict: Dictionary with 'suspicious_combinations' list
    """
    suspicious_combinations = []
    
    MAX_DISTANCE_FOR_SHORT_RIDE = 20.0  # km
    MIN_DURATION_FOR_LONG_RIDE = 5.0    # minutes
    MIN_DISTANCE_FOR_LONG_RIDE = 0.2    # km
    MAX_DURATION_FOR_SHORT_RIDE = 120.0  # minutes
    
    for record in records:
        try:
            distance = float(record.get("distance_km", ""))
            duration = float(record.get("duration_minutes", ""))
            
            # Check: High distance with very short duration
            if distance > MAX_DISTANCE_FOR_SHORT_RIDE and duration < MIN_DURATION_FOR_LONG_RIDE:
                suspicious_combinations.append({
                    "ride_id": record.get("ride_id", ""),
                    "type": "high_distance_short_duration",
                    "distance_km": distance,
                    "duration_minutes": duration,
                    "speed_kph": (distance / duration) * 60 if duration > 0 else 0
                })
            
            # Check: Very low distance with very long duration
            elif distance < MIN_DISTANCE_FOR_LONG_RIDE and duration > MAX_DURATION_FOR_SHORT_RIDE:
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
    Anomaly Rule 1: Duplicate Ride ID
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
    Anomaly Rule 11: Unknown Stations
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
        if not start_station or not end_station:
            unknown_station_records.append(record)
    
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
    results["bike_overlaps"] = detect_bike_overlaps(records)

    print("  - Detecting station spikes...")
    results["station_spike"] = detect_station_spike(records)
    
    print("  - Detecting route spikes...")
    results["route_spike"] = detect_route_spike(records)

    print("  - Detecting zero duration rides...")
    results["zero_duration"] = detect_zero_duration_rides(records)
    
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


# def generate_anomaly_report(results, output_file="reports/anomaly_report.txt"):
#     """
#     Generate a readable anomaly report for the City Mobility Operations Analyst.
    
#     Args:
#         results: Dictionary containing all anomaly detection results
#         output_file: Path to write the report
#     """
#     with open(output_file, "w") as f:
#         f.write("=" * 60 + "\n")
#         f.write("CITY BIKE RIDE ANOMALY REPORT\n")
#         f.write("=" * 60 + "\n\n")
        
#         # Station Spike Anomalies
#         f.write("STATION SPIKE ANOMALIES\n")
#         f.write("-" * 40 + "\n")
#         station_spike = results.get("station_spike", {})
        
#         f.write(f"Average start station usage: {station_spike.get('avg_start_usage', 0):.2f} rides\n")
#         f.write(f"Average end station usage: {station_spike.get('avg_end_usage', 0):.2f} rides\n\n")
        
#         spiked_start = station_spike.get("spiked_start_stations", [])
#         if spiked_start:
#             f.write("Start stations with unusual spikes (>3x average):\n")
#             for station in spiked_start:
#                 f.write(f"  - {station['station']}: {station['count']} rides (ratio: {station['ratio']:.2f}x)\n")
#         else:
#             f.write("No start station spikes detected.\n")
        
#         f.write("\n")
        
#         spiked_end = station_spike.get("spiked_end_stations", [])
#         if spiked_end:
#             f.write("End stations with unusual spikes (>3x average):\n")
#             for station in spiked_end:
#                 f.write(f"  - {station['station']}: {station['count']} rides (ratio: {station['ratio']:.2f}x)\n")
#         else:
#             f.write("No end station spikes detected.\n")
        
#         f.write("\n\n")
        
#         # Route Spike Anomalies
#         f.write("ROUTE SPIKE ANOMALIES\n")
#         f.write("-" * 40 + "\n")
#         route_spike = results.get("route_spike", {})
        
#         f.write(f"Average route usage: {route_spike.get('avg_route_usage', 0):.2f} rides\n")
#         f.write(f"Total unique routes: {route_spike.get('total_routes', 0)}\n\n")
        
#         spiked_routes = route_spike.get("spiked_routes", [])
#         if spiked_routes:
#             f.write("Routes with unusual spikes (>3x average):\n")
#             for route in spiked_routes[:10]:  # Top 10
#                 f.write(f"  - {route['route']}: {route['count']} rides (ratio: {route['ratio']:.2f}x)\n")
#         else:
#             f.write("No route spikes detected.\n")
        
#         f.write("\n\n")
        
#         # Strange Distance/Duration Combinations
#         f.write("STRANGE DISTANCE/DURATION COMBINATIONS\n")
#         f.write("-" * 40 + "\n")
#         strange_combo = results.get("strange_distance_duration", {})
        
#         total_suspicious = strange_combo.get("total_suspicious", 0)
#         f.write(f"Total suspicious combinations: {total_suspicious}\n\n")
        
#         suspicious = strange_combo.get("suspicious_combinations", [])
#         if suspicious:
#             f.write("Sample suspicious records:\n")
#             for record in suspicious[:10]:  # Show first 10
#                 f.write(f"  - Ride {record['ride_id']}: {record['type']}\n")
#                 f.write(f"    Distance: {record['distance_km']} km, Duration: {record['duration_minutes']} min\n")
#                 f.write(f"    Speed: {record['speed_kph']:.2f} km/h\n")
#         else:
#             f.write("No strange distance/duration combinations detected.\n")
        
#         f.write("\n\n")
        
#         # Bikes with Most Suspicious Records
#         f.write("BIKES WITH MOST SUSPICIOUS RECORDS\n")
#         f.write("-" * 40 + "\n")
#         bikes_suspicious = results.get("bikes_with_suspicious", {})
        
#         f.write(f"Total bikes with suspicious records: {bikes_suspicious.get('total_bikes_with_suspicious', 0)}\n\n")
        
#         top_bikes = bikes_suspicious.get("top_suspicious_bikes", [])
#         if top_bikes:
#             f.write("Top 5 bikes by suspicious record count:\n")
#             for bike in top_bikes:
#                 f.write(f"  - {bike['bike_id']}: {bike['suspicious_count']} suspicious records\n")
#         else:
#             f.write("No bikes with suspicious records detected.\n")
        
#         f.write("\n\n")
        
#         # Stations with Most Suspicious Records
#         f.write("STATIONS WITH MOST SUSPICIOUS RECORDS\n")
#         f.write("-" * 40 + "\n")
#         stations_suspicious = results.get("stations_with_suspicious", {})
        
#         top_start = stations_suspicious.get("top_suspicious_start_stations", [])
#         if top_start:
#             f.write("Top 5 start stations by suspicious record count:\n")
#             for station in top_start:
#                 f.write(f"  - {station['station']}: {station['suspicious_count']} suspicious records\n")
#         else:
#             f.write("No start stations with suspicious records.\n")
        
#         f.write("\n")
        
#         top_end = stations_suspicious.get("top_suspicious_end_stations", [])
#         if top_end:
#             f.write("Top 5 end stations by suspicious record count:\n")
#             for station in top_end:
#                 f.write(f"  - {station['station']}: {station['suspicious_count']} suspicious records\n")
#         else:
#             f.write("No end stations with suspicious records.\n")
        
#         f.write("\n\n")
        
#         # Duplicate Ride IDs
#         f.write("DUPLICATE RIDE IDs\n")
#         f.write("-" * 40 + "\n")
#         duplicates = results.get("duplicate_ride_ids", {})
        
#         total_duplicates = duplicates.get("total_duplicates", 0)
#         f.write(f"Total duplicate ride IDs: {total_duplicates}\n\n")
        
#         duplicate_list = duplicates.get("duplicate_ride_ids", [])
#         if duplicate_list:
#             f.write("Duplicate ride IDs:\n")
#             for dup in duplicate_list[:10]:  # Show first 10
#                 f.write(f"  - {dup['ride_id']}: {dup['count']} occurrences\n")
#         else:
#             f.write("No duplicate ride IDs detected.\n")
        
#         f.write("\n\n")
        
#         # Summary and Recommendations
#         f.write("=" * 60 + "\n")
#         f.write("SUMMARY AND RECOMMENDATIONS\n")
#         f.write("=" * 60 + "\n\n")
        
#         recommendations = []
        
#         if spiked_start or spiked_end:
#             recommendations.append("- Investigate stations with usage spikes - may indicate special events or data issues")
        
#         if spiked_routes:
#             recommendations.append("- Review spiked routes - may reveal popular commute patterns or data collection problems")
        
#         if total_suspicious > 0:
#             recommendations.append(f"- Review {total_suspicious} records with impossible distance/duration combinations")
        
#         if top_bikes:
#             recommendations.append("- Check bikes with high suspicious record counts for sensor or checkout system issues")
        
#         if top_start or top_end:
#             recommendations.append("- Investigate stations with high suspicious record involvement for data collection problems")
        
#         if total_duplicates > 0:
#             recommendations.append(f"- Resolve {total_duplicates} duplicate ride IDs to prevent double-counting in reports")
        
#         if recommendations:
#             f.write("Recommended Actions:\n")
#             for rec in recommendations:
#                 f.write(f"{rec}\n")
#         else:
#             f.write("No significant anomalies detected. Data quality appears good.\n")
        
#         f.write("\n")
#         f.write("=" * 60 + "\n")
#         f.write("End of Report\n")
#         f.write("=" * 60 + "\n")
    
#     print(f"Anomaly report generated -> {output_file}")