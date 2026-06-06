import csv
import random
from datetime import datetime, timedelta
import utils


def generate_ride(ride_id):
    ride_id=f"RIDE-{random.randint(1,100000)}"

    bike_id_prefixes=["BIKE","bike","Bike","BIkE","bIKE","BiKe","BIkE"]
    bike_id_suffixes=str(random.randint(1,5000))

    bike_id = bike_id_prefixes[random.randint(0, len(bike_id_prefixes)-1)] + '-' + bike_id_suffixes

    user_type = random.choice(["member", "casual", "tourist", "vip", "robot", "admin", "maybe"])
    
    start_station = random.choice(list(utils.dict_stations.keys()))

    end_station = random.choice(list(utils.dict_stations.keys()))
    
    start_time = datetime.now() - timedelta(
        days=random.randint(0, 365)
    )
    distance= round(random.uniform(-20.0, 20.0), 2)
    distance= str(distance)
    measurement_units=["km"," "]
    distance_km = distance + measurement_units[random.randint(0,len(measurement_units)-1)]
    
    duration_minutes = round(float(distance_km.replace(measurement_units[0], "")) * random.uniform(1, 10), 1)
     
    endtime_time_below = start_time - timedelta(minutes=random.randint(int(duration_minutes)-10,int(duration_minutes)+10))
    endtime_time_upper = start_time + timedelta(minutes=random.randint(int(duration_minutes)-10,int(duration_minutes)+10))
    end_time = random.choice([endtime_time_below, endtime_time_upper])
    
    
    status = "Unvalidated"
    # formats = [
    #     "%Y/%d/%m %H:%M",   # Y/d/m
    #     "%Y-%m-%d %H:%M",   # normal (kept for mix)
    #     "%d-%m-%Y %H:%M",   # d-m-Y
    #     "%Y/%m/%d %H:%M",   # Y/m/d
    #     "%d/%m/%Y %H:%M",   # d/m/Y
    # ]
    date_format=random.choice(utils.accepted_date_formats)

    
    current_ride=[
        ride_id,
        bike_id,
        user_type,      
        start_station,
        end_station,
        start_time.strftime(date_format),
        end_time.strftime(date_format),
        duration_minutes,
        distance_km,
        status
    ]
    # Messiness Starter

    if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_SPACES: #only 10% of rides will have spaces
        current_ride = introduce_spaces(current_ride)
    if random.random() < utils.PROBABILITY_RECORD_WILL_LACK_BIKE_ID: #only 10% of rides will lack bike_id
        current_ride[1] = ""
    if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_INVALID_STATIONS: #only 10% of rides will have invalid station names
        current_ride = create_invalid_station_names(current_ride)
    if random.random() < utils.PROBABILITY_RECORD_WILL_MISSING_STATIONS: #only 10% of rides will have missing Start station
        current_ride[3] = ""
    if random.random() < utils.PROBABILITY_RECORD_WILL_MISSING_STATIONS: #only 10% of rides will have missing End station
        current_ride[4] = ""
    if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_INVALID_FORMATING: #only 10% of rides will have invalid formatting
        current_ride = inconsistent_name_formating(current_ride)
    if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_INVALID_BIKE_IDS: #only 10% of rides will have invalid bike ids
        current_ride = invalid_bike_ids(current_ride)
    if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_INVALID_DURATION: #only 10% of rides will have invalid duration
        current_ride = invalid_durations(current_ride)
    if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_INVALID_USER_TYPE: #only 10% of rides will have inconsistent user type capitalization
        current_ride = inconsistent_user_type_capitalization(current_ride)
    
    return current_ride


def introduce_spaces(ride):
    for i, field in enumerate(ride):
        field = str(field)

        if field == "Unvalidated":
            continue
        
        for j in range(len(field)):
            if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_SPACES:  # 10% chance to add a space
                field = field[:j] + ' ' + field[j:]

        ride[i] = field
        
    return ride


def create_invalid_station_names(ride):
    start_station = ride[3]
    end_station = ride[4]
    
    new_start_station_len = random.randint(1, len(start_station))
    new_end_station_len = random.randint(1, len(end_station))
    
    start_station = ""
    for i in range(new_start_station_len):
        start_station += chr(random.randint(45, 125)) # 45 to avoid messing up the CSV by adding random commas or quotes

    end_station = ""
    for i in range(new_end_station_len):
        end_station += chr(random.randint(45, 125)) # 45 to avoid messing up the CSV by adding random commas or quotes
    
    ride[3] = start_station
    ride[4] = end_station
    
    return ride

def inconsistent_name_formating(ride):
    start_station = ride[3]
    end_station = ride[4]

    new_start_station = ""
    for i in range(len(start_station)):
        if random.random() < len(start_station):
            new_start_station += start_station[i].upper()
        if random.random() == len(start_station):
            new_start_station += start_station[i].lower()

    new_end_station = ""
    for i in range(len(end_station)):
        if random.random() < len(end_station):
            new_end_station += end_station[i].upper()
        if random.random() == len(end_station):
            new_end_station += end_station[i].lower()

    ride[3] = new_start_station
    ride[4] = new_end_station

    return ride

def invalid_bike_ids(ride):
    bike_id = ride[1]
    if "-" not in bike_id:
        return ride 

    prefix_id, suffix_id = bike_id.split("-", 1)
    
    new_suffix_id = ""

    for i in range(len(suffix_id)):
        if random.random() < len(suffix_id):
            new_suffix_id = ""
            new_suffix_id += chr(random.randint(ord('A'), ord('Z')))
        if random.random() < len(suffix_id):
            new_suffix_id += suffix_id[i]
    
    ride[1] = prefix_id + "-" + new_suffix_id
    return ride


def invalid_durations(ride):
    ride[7] = ""
    return ride

def inconsistent_user_type_capitalization(ride):
    user_type = ride[2]
    
    new_user_type = ""
    for i in range(len(user_type)):
        if random.randint(0, len(user_type)) < len(user_type) / 2:
            new_user_type += user_type[i].upper()
        else:
            new_user_type += user_type[i].lower()
    
    ride[2] = new_user_type
    return ride

def create_dataset(filename, num_rows):
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "ride_id",
            "bike_id",
            "user_type",
            "start_station",
            "end_station",
            "start_time",
            "end_time",
            "duration_minutes",
            "distance_km",
            "status"
        ])

        for ride_id in range(1, num_rows + 1):
            writer.writerow(generate_ride(ride_id))

create_dataset("data/bike_rides.csv", 10000)