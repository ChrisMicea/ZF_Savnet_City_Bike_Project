# Assigns a status to each record and determines if: it is clean, needs cleaning or is beyond repair (ex: missing fields etc.)

import csv, re
import utils
from datetime import datetime

VALIDATION_STATUS = {
    0: "beyond_repair",
    1: "clean",
    2: "needs_cleaning"
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
            # status = validate_start_station(row)
            # validate_end_station(row)
            status = validate_start_time(row)
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

def validate_start_station(record: dict) -> str:
    pass

def validate_end_station(record: dict) -> str:
    pass

def validate_start_time(record: dict) -> str:
    start_time = record.get("start_time")

    # if date has spaces, mark as needs_cleaning
    if " " in start_time:
        start_time = start_time.strip()
    
    # now add back the space standing between dd-mm-yy and hh-mm
    

    # if the date format is invalid, mark as needs_cleaning
    try:
        datetime.strptime(start_time, "%d-%m-%Y %H:%M")
    except ValueError:
        return VALIDATION_STATUS[2]
    
    return VALIDATION_STATUS[1]

def validate_end_time(record: dict) -> str:
    end_time = record.get("end_time")
    # if the date format is invalid, mark as needs_cleaning
    try:
        datetime.strptime(end_time, "%d-%m-%Y %H:%M")
    except ValueError:
        return VALIDATION_STATUS[2]
    # if date has spaces, mark as needs_cleaning

def validate_duration(record: dict) -> str:
    pass