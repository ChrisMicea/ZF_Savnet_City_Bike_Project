import csv
import re
import utils
from datetime import datetime


VALIDATION_STATUS = {
    "clean": 0,
    "needs_cleaning": 1,
    "suspicious": 2,
    "beyond_repair": 3
}
VALIDATION_STATUS_FOR_WRITE = {
    0: "clean",
    1: "needs_cleaning",
    2: "suspicious",
    3: "beyond_repair"
}


ride_ids_encountered = set()


def worst_status(a, b):
    """Return the worse of two statuses (higher = worse)."""
    return max(a, b)


def validate_records(csv_input: str):
    # First pass: read all rows into memory
    with open(csv_input, "r", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Second pass: validate and write back with status column
    with open(csv_input, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames + ["status"])
        writer.writeheader()

        for idx, row in enumerate(rows):
            status = VALIDATION_STATUS["clean"]

            status = worst_status(status, validate_ride_id(row))
            status = worst_status(status, validate_bike_id(row))
            status = worst_status(status, validate_user_type(row))
            status = worst_status(status, validate_station(row, 0))
            status = worst_status(status, validate_station(row, 1))
            status = worst_status(status, validate_start_time(row))
            status = worst_status(status, validate_end_time(row))
            status = worst_status(status, validate_duration(row))
            status = worst_status(status, validate_distance(row))

            row["status"] = VALIDATION_STATUS_FOR_WRITE[status]
            writer.writerow(row)

            print(f"Record #{idx} has status {status}")


def validate_ride_id(record: dict) -> int:
    ride_id = record.get("ride_id")
    if not ride_id:
        return VALIDATION_STATUS["beyond_repair"]

    needs_cleaning = False

    if " " in ride_id:
        ride_id = ride_id.replace(" ", "")
        needs_cleaning = True

    if not re.match(r"^RIDE-\d{5}$", ride_id):
        return VALIDATION_STATUS["beyond_repair"]

    if ride_id in ride_ids_encountered:
        return VALIDATION_STATUS["suspicious"]

    ride_ids_encountered.add(ride_id)

    return VALIDATION_STATUS["needs_cleaning"] if needs_cleaning else VALIDATION_STATUS["clean"]


def validate_bike_id(record: dict) -> int:
    bike_id = record.get("bike_id")
    if not bike_id:
        return VALIDATION_STATUS["beyond_repair"]

    needs_cleaning = False

    if " " in bike_id:
        bike_id = bike_id.replace(" ", "")
        needs_cleaning = True

    if not re.match(r"^[Bb][Ii][Kk][Ee]-\d{4}$", bike_id):
        return VALIDATION_STATUS["beyond_repair"]

    normalized = "BIKE-" + bike_id.split("-")[1]
    if bike_id != normalized:
        needs_cleaning = True

    return VALIDATION_STATUS["needs_cleaning"] if needs_cleaning else VALIDATION_STATUS["clean"]


def validate_user_type(record: dict) -> int:
    user_type = record.get("user_type")
    if not user_type:
        return VALIDATION_STATUS["beyond_repair"]

    needs_cleaning = False

    if " " in user_type:
        user_type = user_type.replace(" ", "")
        needs_cleaning = True

    if user_type != user_type.lower():
        user_type = user_type.lower()
        needs_cleaning = True

    if user_type not in utils.valid_user_types:
        return VALIDATION_STATUS["beyond_repair"]

    return VALIDATION_STATUS["needs_cleaning"] if needs_cleaning else VALIDATION_STATUS["clean"]


def validate_station(record: dict, start_or_end: int) -> int:
    key = "start_station" if start_or_end == 0 else "end_station"
    station = record.get(key)

    if not station:
        return VALIDATION_STATUS["beyond_repair"]

    needs_cleaning = False

    station = station.replace(" ", "")
    if station != record.get(key):
        needs_cleaning = True

    if station != station.title():
        needs_cleaning = True
        station = station.title()

    if not re.match(r"^[A-Za-z_]+$", station):
        return VALIDATION_STATUS["beyond_repair"]

    if station not in utils.dict_stations:
        return VALIDATION_STATUS["suspicious"]

    return VALIDATION_STATUS["needs_cleaning"] if needs_cleaning else VALIDATION_STATUS["clean"]


def validate_start_time(record: dict) -> int:
    return _validate_datetime(record.get("start_time"))


def validate_end_time(record: dict) -> int:
    return _validate_datetime(record.get("end_time"))


def _validate_datetime(value: str) -> int:
    if not value:
        return VALIDATION_STATUS["beyond_repair"]

    value = value.replace(" ", "")
    value = value[:10] + " " + value[10:]

    for fmt in utils.accepted_date_formats:
        try:
            datetime.strptime(value, fmt)
            break
        except ValueError:
            continue
    else:
        return VALIDATION_STATUS["beyond_repair"]

    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M")
        return VALIDATION_STATUS["clean"]
    except ValueError:
        return VALIDATION_STATUS["needs_cleaning"]


def validate_duration(record: dict) -> int:
    value = record.get("duration_minutes")
    if not value:
        return VALIDATION_STATUS["beyond_repair"]

    needs_cleaning = False

    if " " in value:
        value = value.replace(" ", "")
        needs_cleaning = True

    for digit in value:
        if not digit.isdigit() and digit != "-" and digit != ".":
            return VALIDATION_STATUS["beyond_repair"]

    if float(value) < 0:
        return VALIDATION_STATUS["beyond_repair"]

    return VALIDATION_STATUS["needs_cleaning"] if needs_cleaning else VALIDATION_STATUS["clean"]


def validate_distance(record: dict) -> int:
    value = record.get("distance_km")
    if not value:
        return VALIDATION_STATUS["beyond_repair"]

    needs_cleaning = False

    if " " in value:
        value = value.replace(" ", "")
        needs_cleaning = True

    if "km" in value.lower():
        value = value.lower().replace("km", "")
        needs_cleaning = True

    value = value.replace(" ", "")

    for digit in value:
        if not digit.isdigit() and digit != "-" and digit != ".":
            return VALIDATION_STATUS["beyond_repair"]

    if float(value) < 0:
        return VALIDATION_STATUS["beyond_repair"]

    return VALIDATION_STATUS["needs_cleaning"] if needs_cleaning else VALIDATION_STATUS["clean"]