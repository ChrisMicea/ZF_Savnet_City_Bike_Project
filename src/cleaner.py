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

# import csv
# from datetime import datetime
# import utils

# def clean_data(input_file="data/bike_rides.csv", output_file="data/bike_rides_cleaned.csv"):
#     # Read all rows into memory
#     with open(input_file, "r") as infile:
#         reader = csv.DictReader(infile)
#         fieldnames = reader.fieldnames
#         rows = list(reader)
    
#     cleaned_rows = [] 
    
#     for row in rows:
#         status = row.get("status", "")
        
#         # Only clean rows with status "needs_cleaning" or "suspicious"
#         if status in ["needs_cleaning", "suspicious"]:
#             # Apply cleaning transformations
#             row = clean_ride_id(row)
#             row = clean_bike_id(row)
#             row = clean_user_type(row)
#             row = clean_station(row, "start_station")
#             row = clean_station(row, "end_station")
#             row = clean_start_time(row)
#             row = clean_end_time(row)
#             row = clean_distance(row)
#             row = clean_spaces(row)
            
#             # Replace "needs_cleaning" with "fixed"
#             if status == "needs_cleaning":
#                 row["status"] = "fixed"
        
#         cleaned_rows.append(row)
    
#     # Sort by status (clean -> fixed -> suspicious -> beyond_repair), then by ride_id
#     def sort_key(row):
#         status_order = {"clean": 0, "fixed": 1, "suspicious": 2, "beyond_repair": 3}
#         return (status_order.get(row.get("status", "beyond_repair"), 3), row.get("ride_id", ""))
    
#     cleaned_rows.sort(key=sort_key)
    
#     # Write cleaned data
#     with open(output_file, "w", newline="") as outfile:
#         writer = csv.DictWriter(outfile, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(cleaned_rows)


# def clean_spaces(record: dict):
#     # remove spaces from all fields except start_time and end_time
#     for key, value in record.items():
#         if value and key not in ["start_time", "end_time"]:
#             record[key] = value.replace(" ", "")
#     return record

# def clean_ride_id(record: dict):
#     # convert ride_id to uppercase
#     ride_id = record.get("ride_id")
#     if ride_id:
#         record["ride_id"] = ride_id.upper()
#     return record

# def clean_bike_id(record: dict):
#     # convert bike_id to uppercase
#     bike_id = record.get("bike_id")
#     if bike_id:
#         record["bike_id"] = bike_id.upper()
#     return record

# def clean_user_type(record: dict):
#     # convert user_type to lowercase
#     user_type = record.get("user_type")
#     if user_type:
#         record["user_type"] = user_type.lower()
#     return record

# def clean_station(record: dict, station_key: str):
#     # convert station name to titlecase
#     station = record.get(station_key)
#     if station:
#         record[station_key] = station.title()
#     return record

# def clean_start_time(record: dict):
#     # normalize start_time to %Y-%m-%d %H:%M format
#     start_time = record.get("start_time")
#     if start_time:
#         record["start_time"] = normalize_datetime(start_time)
#     return record

# def clean_end_time(record: dict):
#     # normalize end_time to %Y-%m-%d %H:%M format
#     end_time = record.get("end_time")
#     if end_time:
#         record["end_time"] = normalize_datetime(end_time)
#     return record

# def clean_distance(record: dict):
#     # remove 'km' from distance_km field
#     distance = record.get("distance_km")
#     if distance:
#         distance = distance.lower().replace("km", "").strip()
#         record["distance_km"] = distance
#     return record

# def normalize_datetime(value: str) -> str:
#     # try to parse datetime with various formats and return in %Y-%m-%d %H:%M format
#     # remove spaces first
#     value = value.replace(" ", "")
    
#     for fmt in utils.accepted_date_formats:
#         try:
#             dt = datetime.strptime(value, fmt)
#             return dt.strftime("%Y-%m-%d %H:%M")
#         except ValueError:
#             continue
    
#     # If no format matches, return original value
#     return value
import csv
import re
from datetime import datetime
import utils
import validator

# Inject "fixed" into validator's status scheme (cleaner-only status)
validator.VALIDATION_STATUS["fixed"] = 4
validator.VALIDATION_STATUS_FOR_WRITE[4] = "fixed"

# Global state for cross-record checks
_ride_ids_seen  = set()
_bike_intervals = {}   # bike_id -> [(start_time, end_time)]

# Thresholds
MAX_RIDE_DURATION_MINUTES        = 600
MIN_SPEED_KPH                    = 2.0
MAX_SPEED_KPH                    = 60.0
DURATION_TIMESTAMP_TOLERANCE_MIN = 15


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
            row = clean_start_time(row)
            row = clean_end_time(row)
            row = clean_duration(row)
            row = clean_distance(row)
            row = check_cross_fields(row)

            if status == "needs_cleaning" and row["status"] not in ["beyond_repair", "suspicious"]:
                row["status"] = "fixed"
        else:
            _register_ride(row)

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


#???
def _register_ride(record: dict):
    """Register ride_id and bike interval for rows that are skipped during cleaning."""
    ride_id = record.get("ride_id", "").replace(" ", "").upper()
    if re.match(r"^RIDE-\d{5}$", ride_id):
        _ride_ids_seen.add(ride_id)

    bike_id  = record.get("bike_id", "").replace(" ", "")
    start_time = _parse_datetime(record.get("start_time", ""))
    end_time   = _parse_datetime(record.get("end_time", ""))
    if bike_id and start_time and end_time and end_time > start_time:
        _bike_intervals.setdefault(bike_id, []).append((start_time, end_time))

#???
def _parse_datetime(value: str):
    """Try all accepted formats, return datetime or None."""
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
    # convert ride_id to uppercase and check the invalid format as beyond_repair
    ride_id = record.get("ride_id")

    if not ride_id:
        record["status"] = "beyond_repair"
        return record

    ride_id = ride_id.upper()

    #???
    if not re.match(r"^RIDE-\d{5}$", ride_id):
        record["status"] = "beyond_repair"
        return record

    if ride_id in _ride_ids_seen:
        record["status"] = "beyond_repair"
        return record

    _ride_ids_seen.add(ride_id)
    record["ride_id"] = ride_id
    return record


def clean_bike_id(record: dict):
    # convert bike_id prefix to uppercase and validate the correct format (BIKE-4digits)
    if record.get("status") == "beyond_repair":
        return record

    bike_id = record.get("bike_id")

    if not bike_id:
        record["status"] = "beyond_repair"
        return record

    if not re.match(r"^[Bb][Ii][Kk][Ee]-\d{4}$", bike_id):
        record["status"] = "beyond_repair"
        return record

    record["bike_id"] = "BIKE-" + bike_id.split("-", 1)[1]
    return record


def clean_user_type(record: dict):
    # convert user_type to lowercase and checks the correct format
    if record.get("status") == "beyond_repair":
        return record

    user_type = record.get("user_type")

    if not user_type:
        record["status"] = "beyond_repair"
        return record

    user_type = user_type.lower()

    if user_type not in utils.valid_user_types:
        record["status"] = "beyond_repair"
        return record

    record["user_type"] = user_type
    return record


def clean_station(record: dict, station_key: str):
    # convert station name to titlecase and check the correct format, writing unknown stations as "suspicious"
    if record.get("status") == "beyond_repair":
        return record

    station = record.get(station_key)

    if not station:
        record["status"] = "beyond_repair"
        return record

    station = station.title()

    if not re.match(r"^[A-Za-z_]+$", station):
        record["status"] = "beyond_repair"
        return record

    record[station_key] = station

    if station not in utils.dict_stations:
        record["status"] = "suspicious"

    return record


def clean_start_time(record: dict):
    # normalize start_time to %Y-%m-%d %H:%M format
    if record.get("status") == "beyond_repair":
        return record

    start_time = record.get("start_time")

    if not start_time:
        record["status"] = "beyond_repair"
        return record

    normalized = normalize_datetime(start_time)

    if normalized is None:
        record["status"] = "beyond_repair"
        return record

    record["start_time"] = normalized
    return record


def clean_end_time(record: dict):
    # normalize end_time to %Y-%m-%d %H:%M format
    if record.get("status") == "beyond_repair":
        return record

    end_time = record.get("end_time")

    if not end_time:
        record["status"] = "beyond_repair"
        return record

    normalized = normalize_datetime(end_time)

    if normalized is None:
        record["status"] = "beyond_repair"
        return record

    record["end_time"] = normalized
    return record


def clean_duration(record: dict):
    # checking for missing, non-numeric, negative, zero, or extremely long -> beyond_repair
    if record.get("status") == "beyond_repair":
        return record

    duration = record.get("duration_minutes")

    if not duration:
        record["status"] = "beyond_repair"
        return record

    if not re.match(r"^-?\d+(\.\d+)?$", duration):
        record["status"] = "beyond_repair"
        return record

    duration_val = float(duration)

    if duration_val <= 0:
        record["status"] = "beyond_repair"
        return record

    if duration_val > MAX_RIDE_DURATION_MINUTES:
        record["status"] = "beyond_repair"
        return record

    return record


def clean_distance(record: dict):
    # remove 'km' from distance_km field
    # guard: missing, non-numeric, or negative -> beyond_repair
    if record.get("status") == "beyond_repair":
        return record

    distance = record.get("distance_km")

    if not distance:
        record["status"] = "beyond_repair"
        return record

    distance = distance.lower().replace("km", "").strip()

    if not re.match(r"^-?\d+(\.\d+)?$", distance):
        record["status"] = "beyond_repair"
        return record

    if float(distance) < 0:
        record["status"] = "beyond_repair"
        return record

    record["distance_km"] = distance
    return record


def check_cross_fields(record: dict):
    # checking all fields together
    if record.get("status") == "beyond_repair":
        return record

    start_time = _parse_datetime(record.get("start_time", ""))
    end_time   = _parse_datetime(record.get("end_time", ""))

    if start_time is None or end_time is None:
        record["status"] = "beyond_repair"
        return record

    if end_time <= start_time:
        record["status"] = "beyond_repair"
        return record

    timestamp_diff_in_minutes = (end_time - start_time).total_seconds() / 60.0

    try:
        duration = float(record.get("duration_minutes", ""))
        if abs(duration - timestamp_diff_in_minutes) > DURATION_TIMESTAMP_TOLERANCE_MIN:
            record["status"] = "beyond_repair"
            return record
    except (ValueError, TypeError):
        pass

    try:
        distance  = float(record.get("distance_km", ""))
        speed_kph = (distance / timestamp_diff_in_minutes) * 60.0 if timestamp_diff_in_minutes > 0 else 0
        if speed_kph < MIN_SPEED_KPH or speed_kph > MAX_SPEED_KPH:
            record["status"] = "suspicious"
    except (ValueError, TypeError):
        pass

    bike_id = record.get("bike_id", "")
    if bike_id:
        for existing_start, existing_end in _bike_intervals.get(bike_id, []):
            if start_time < existing_end and end_time > existing_start:
                record["status"] = "beyond_repair"
                return record
        _bike_intervals.setdefault(bike_id, []).append((start_time, end_time))

    return record


def normalize_datetime(value: str):
    # try to parse datetime with various formats and return in %Y-%m-%d %H:%M format
    # returns None if no format matches (instead of silently returning original)
    if not value:
        return None

    value = value.replace(" ", "")
    value = value[:10] + " " + value[10:]

    for fmt in utils.accepted_date_formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue

    return None  # no format matched — caller will set beyond_repair