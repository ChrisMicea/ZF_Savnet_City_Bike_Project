# # cleaning and generating new csv file with cleaned data
# # 
# # where the status is "needs_cleaning" or "suspicious", normalize the data, delete spaces, ride_id to uppercase,
# # bike_id to uppercase, user_type to lowercase, station_name to titlecase, start_time and end_time in %Y-%m-%d %H:%M format
# # remove "km" from distance.
# # replace "needs_cleaning" with "fixed" in status and "suspicious" as it is.
# # Do not silently fix:
# # Missing required fields.
# # Duplicate ride IDs.   
# # Negative durations.
# # Zero durations.
# # End times before start times.
# # Invalid dates.
# # Unknown user types.
# # Negative distances.
# # Bikes with overlapping rides.
# # Duration values that strongly disagree with timestamps.
# # Extremely long rides.
# # Impossible distance and duration combinations.
# # after cleaning the data, sort it by status first, starting with "clean" -> "fixed" -> "suspicious" -> "beyond_repair"
# # then by ride_id

import csv
from datetime import datetime
import utils
import validator

validator.VALIDATION_STATUS["fixed"] = 4
validator.VALIDATION_STATUS_FOR_WRITE[4] = "fixed"

_ride_ids_seen  = set()
_bike_intervals = {} 

def clean_data(input_file="data/bike_rides.csv", output_file="data/bike_rides_cleaned.csv"):
    with open(input_file, "r") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        rows = list(reader)

    cleaned_rows = []

    for row in rows:
        status = row.get("status", "")

        if status in ["needs_cleaning", "suspicious"]:
            row = clean_spaces(row)
            row = clean_ride_id(row)
            row = clean_bike_id(row)
            row = clean_user_type(row)
            row = clean_station(row, "start_station")
            row = clean_station(row, "end_station")
            row = clean_time(row, 0)
            row = clean_time(row, 1)
            row = clean_duration(row)
            row = clean_distance(row)
            row = check_cross_fields(row)

            if status == "needs_cleaning" and row["status"] not in ["beyond_repair", "suspicious"]:
                row["status"] = "fixed"
        
        cleaned_rows.append(row)

    def sort_key(row):
        status_order = {"clean": 0, "fixed": 1, "suspicious": 2, "beyond_repair": 3}
        return (status_order.get(row.get("status", "beyond_repair"), 3), row.get("ride_id", ""))

    cleaned_rows.sort(key=sort_key)

    with open(output_file, "w", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    counts = {"clean": 0, "fixed": 0, "suspicious": 0, "beyond_repair": 0}
    for row in cleaned_rows:
        counts[row.get("status", "beyond_repair")] += 1

    print(f"Cleaning complete -> {output_file}")
    print(f"  clean        : {counts['clean']}")
    print(f"  fixed        : {counts['fixed']}")
    print(f"  suspicious   : {counts['suspicious']}")
    print(f"  beyond_repair: {counts['beyond_repair']}")

def _parse_datetime(value: str):
    # accept formats, return datetime or None
    if not value:
        return None
    value = value.replace(" ", "")
    value = value[:10] + " " + value[10:]
    for fmt in utils.accepted_date_formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def clean_spaces(record: dict):
    # remove spaces from all fields except start_time and end_time
    for key, value in record.items():
        if value and key not in ["start_time", "end_time"]:
            record[key] = value.replace(" ", "")
    return record


def clean_ride_id(record: dict):
    # convert ride_id to uppercase
    ride_id = record.get("ride_id")

    ride_id = ride_id.upper()

    _ride_ids_seen.add(ride_id)
    record["ride_id"] = ride_id
    return record

def clean_bike_id(record: dict):
    # convert bike_id prefix to uppercase and validate the correct format (BIKE-4digits)
    bike_id = record.get("bike_id")

    record["bike_id"] = "BIKE-" + bike_id.split("-", 1)[1]
    return record

def clean_user_type(record: dict):
    # convert user_type to lowercase and checks the correct format
    user_type = record.get("user_type")

    user_type = user_type.lower()

    record["user_type"] = user_type
    return record

def clean_station(record: dict, station_key: str):
    # convert station name to titlecase and check the correct format, writing unknown stations as "suspicious"
    station = record.get(station_key)
    station = station.title()

    record[station_key] = station

    return record


def clean_time(record: dict, start_or_end: int):
    # normalize start_time to %Y-%m-%d %H:%M format
    key = "start_time" if start_or_end == 0 else "end_time"
    time_value = record.get(key)

    normalized = normalize_datetime(time_value)

    record[key] = normalized
    return record

def clean_duration(record: dict):
    # checking for missing, non-numeric, negative, zero, or extremely long -> beyond_repair
    duration = record.get("duration_minutes")

    duration_val = float(duration)

    if duration_val == 0:
        record["status"] = "suspicious"
        return record

    if duration_val > utils.MAX_RIDE_DURATION_MINUTES:
        record["status"] = "suspicious"
        return record

    return record


def clean_distance(record: dict):
    # remove 'km' from distance_km field
    distance = record.get("distance_km")

    distance = distance.lower().replace("km", "").strip()

    record["distance_km"] = distance
    return record


def check_cross_fields(record: dict):
    # checking all fields together, check if the start or end time is greater than the current time
    # also check if the recorded duration differes from the calculated distance by more than TOLERANCE_MIN
    start_time = _parse_datetime(record.get("start_time", ""))
    end_time   = _parse_datetime(record.get("end_time", ""))

    if end_time < start_time:
        record["status"] = "beyond_repair"
        return record

    timestamp_diff_in_minutes = (end_time - start_time).total_seconds() / 60.0

    try:
        duration = float(record.get("duration_minutes", ""))
        if abs(duration - timestamp_diff_in_minutes) > utils.DURATION_TIMESTAMP_TOLERANCE_MIN:
            record["status"] = "suspicious"
            return record
    except (ValueError, TypeError):
        pass

    try:
        distance  = float(record.get("distance_km", ""))
        speed_kph = (distance / timestamp_diff_in_minutes) * 60.0 if timestamp_diff_in_minutes > 0 else 0
        if speed_kph < utils.MIN_SPEED_KPH or speed_kph > utils.MAX_SPEED_KPH:
            record["status"] = "suspicious"
    except (ValueError, TypeError):
        pass

    # checks for overlapping rides for the same bike
    bike_id = record.get("bike_id", "")
    if bike_id:
        for existing_start, existing_end in _bike_intervals.get(bike_id, []):
            if start_time < existing_end and end_time > existing_start:
                record["status"] = "suspicious"
                return record
        _bike_intervals.setdefault(bike_id, []).append((start_time, end_time))

    return record


def normalize_datetime(value: str):
    # try to parse datetime with various formats and return in %Y-%m-%d %H:%M format
    # returns None if no format matches (instead of silently returning original)
    value = value.replace(" ", "")
    value = value[:10] + " " + value[10:]

    for fmt in utils.accepted_date_formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue

    return None  # no format matched — caller will set beyond_repair