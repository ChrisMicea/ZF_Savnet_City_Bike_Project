# Assigns a status to each record and determines if: it is clean, needs cleaning or is beyond repair (ex: missing fields etc.)

import csv, re
import utils
from datetime import datetime

VALIDATION_STATUS = {
    0: "beyond_repair",
    1: "clean",
    2: "needs_cleaning",
    3: "suspicious"
}

ride_ids_encountered = set()

def validate_records(csv_input: str):
    with open(csv_input, "r") as file:
        reader = csv.DictReader(file)
        idx = 0
        # print("here")
        for row in reader:
            # status = validate_ride_id(row)
            # status = validate_bike_id(row)
            # status = validate_user_type(row)
            status = validate_station(row, 0)
            # validate_station(row, 1)
            # status = validate_start_time(row)
            # validate_end_time(row)
            # validate_duration(row)
            print(f"Record #{idx} has status {status}")
            idx += 1

def validate_ride_id(record: dict) -> str:
    ride_id = record.get("ride_id")

    if not ride_id:
        return VALIDATION_STATUS[0]
    
    # if the field contains spaces, mark as needs_cleaning and strip the spaces
    has_spaces = False
    if " " in ride_id:
        has_spaces = True
        ride_id = ride_id.strip()

    # ride_id needs to follow a pattern of "RIDE-XXXXX, where X is a digit 0-9"
    if not re.match(r"^RIDE-\d{5}$", ride_id):
        return VALIDATION_STATUS[0]
    
    # verify unicity in the dataset
    if ride_id in ride_ids_encountered:
        return VALIDATION_STATUS[0]
    ride_ids_encountered.add(ride_id)

    return VALIDATION_STATUS[1] if not has_spaces else VALIDATION_STATUS[2]

def validate_bike_id(record: dict) -> str:
    bike_id = record.get("bike_id")

    if not bike_id:
        return VALIDATION_STATUS[0]
    
    # if the field contains spaces, mark as needs_cleaning and strip the spaces
    has_spaces = False
    if " " in bike_id:
        has_spaces = True
        bike_id = bike_id.strip()

    # bike_id needs to follow a pattern of "BIKE-XXXX, where X is a digit 0-9 (BIKE can be capital or not)"
    if not re.match(r"^[Bb][Ii][Kk][Ee]-\d{4}$", bike_id):
        return VALIDATION_STATUS[0]

    # if the initial "BIKE" has inconsistent capitalization, mark as needing cleaning
    if bike_id != "BIKE-" + bike_id.split("-")[1]:
        has_spaces = True
    
    return VALIDATION_STATUS[1] if not has_spaces else VALIDATION_STATUS[2]

def validate_user_type(record: dict) -> str:
    # valid user types: Member, Casual, Tourist
    user_type = record.get("user_type")
    
    if not user_type:
        return VALIDATION_STATUS[0]
    
    # if the field contains spaces, mark as needs_cleaning and strip the spaces
    has_spaces = False
    if " " in user_type:
        has_spaces = True
        user_type = user_type.strip()
    
    # user types should be normalized to lowercase - if they aren't, they need cleaning
    if user_type != user_type.lower():
        has_spaces = True
        user_type = user_type.lower()
    
    # user_type needs to be one of the valid user types
    if user_type not in utils.valid_user_types:
        return VALIDATION_STATUS[0]
    
    return VALIDATION_STATUS[1] if not has_spaces else VALIDATION_STATUS[2]

def validate_station(record: dict, start_or_end_station: int) -> str:
    #not be empty, normalized consistently (no spaces, no special characters, has to have capital letters), contain readable text, missing stations are invalid
    station_key = "start_station" if start_or_end_station == 0 else "end_station"
    station = record.get(station_key)
    if not station:
        return VALIDATION_STATUS[0]
    
    # if the field contains spaces, mark as needs_cleaning and strip the spaces
    needs_cleaning = False
    if " " in station:
        needs_cleaning = True
        station = station.replace(" ", "")

    # start_station must have capital letters
    if station != station.title():
        needs_cleaning = True
        station = station.title()
    
    # start_station names must not contain special characters or numbers and if they do, they are invalid;
    # do not use isalpha() method as i have "_" in the station names
    if not re.match(r"^[A-Za-z_]+$", station):
        return VALIDATION_STATUS[0]

    # if the start_station name is not in the dictionary of valid stations, does not contain special characters or numbers, then it must be flagged as suspicious
    if station not in utils.dict_stations:
        return VALIDATION_STATUS[3]

    # start_station names must be in the dictionary of valid stations
    if station not in utils.dict_stations:
        return VALIDATION_STATUS[0]
    
    return VALIDATION_STATUS[1] if not needs_cleaning else VALIDATION_STATUS[2]

def validate_start_time(record: dict) -> str:
    start_time = record.get("start_time")

    # if date has spaces, mark as needs_cleaning
    if " " in start_time:
        start_time = start_time.replace(" ", "")
    
    # now add back the space standing between dd-mm-yy and hh-mm
    start_time = start_time[:10] + " " + start_time[10:]

    # if the date format is not found in utils.accepted_date_formats, it is invalid / beyond repair
    for format in utils.accepted_date_formats:
        try:
            datetime.strptime(start_time, format)
            break # break skips the latter "else: ... " block
        except ValueError:
            continue
    else:
        return VALIDATION_STATUS[0]
    
    try:
        datetime.strptime(start_time, "%Y-%m-%d %H:%M") # correct format, needs no cleaning
        return VALIDATION_STATUS[1]
    except ValueError:
        return VALIDATION_STATUS[2] # readable datetime format but not the correct / standard one, needs cleaning

def validate_end_time(record: dict) -> str:
    end_time = record.get("end_time")

    # if date has spaces, mark as needs_cleaning
    if " " in end_time:
        end_time = end_time.strip()
    
    # now add back the space standing between dd-mm-yy and hh-mm
    end_time = end_time[:10] + " " + end_time[10:]

    # if the date format is not found in utils.accepted_date_formats, it is invalid / beyond repair
    for format in utils.accepted_date_formats:
        try:
            datetime.strptime(end_time, format)
            break # break skips the latter "else: ... " block
        except ValueError:
            continue
    else:
        return VALIDATION_STATUS[0]
    
    try:
        datetime.strptime(end_time, "%Y-%m-%d %H:%M") # correct format, needs no cleaning
        return VALIDATION_STATUS[1]
    except ValueError:
        return VALIDATION_STATUS[2] # readable datetime format but not the correct / standard one, needs cleaning

def validate_duration(record: dict) -> str:
    #has to be in bike_rides.csv, it must be a number, it must be positive
    duration_id = record.get("duration_minutes")
    if not duration_id:
        return VALIDATION_STATUS[0]
    
    # if the field contains spaces, mark as needs_cleaning and strip the spaces
    needs_cleaning = False
    if " " in duration_id:
        needs_cleaning = True
        duration_id = duration_id.strip()
    
    # check if the field is a number
    if not duration_id.isdigit():
        return VALIDATION_STATUS[0]
    
    # check if the field is positive
    if int(duration_id) < 0:
        return VALIDATION_STATUS[0]
    
    return VALIDATION_STATUS[1] if not needs_cleaning else VALIDATION_STATUS[2]

def validate_distance_(record: dict) -> str:
    #has to be in bike_rides.csv, it must not be a negative value and it must be a number, it can also contain "km" before or after the digits
    distance_id = record.get("distance_km")
    if not distance_id:
        return VALIDATION_STATUS[0]
    
    # if the field contains spaces, mark as needs_cleaning and strip the spaces
    needs_cleaning = False
    if " " in distance_id:
        needs_cleaning = True
        distance_id = distance_id.strip()
    
    # flag "km" from the string if it exists with needs_cleaning
    if "km" in distance_id:
        needs_cleaning = True
    
    # check if the field is a number
    if not distance_id.isdigit():
        return VALIDATION_STATUS[0]
    
    # check if the field is negative
    if int(distance_id) < 0:
        return VALIDATION_STATUS[0]
    
    return VALIDATION_STATUS[1] if not needs_cleaning else VALIDATION_STATUS[2]