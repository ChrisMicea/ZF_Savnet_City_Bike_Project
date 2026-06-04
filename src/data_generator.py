import csv
import random
from datetime import datetime, timedelta
import utils


def generate_ride(ride_id):
    ride_id=f"RIDE-{random.randint(1,10000)}"

    bike_id = f"Bike-{random.randint(1, 5000)}"

    user_type = random.choice(["Member", "Casual","Tourist","VIP","Robot","Admin",""])
    
    start_station = random.choice(list(utils.dict_stations.keys()))

    end_station = random.choice(list(utils.dict_stations.keys()))
    
    start_time = datetime.now() - timedelta(
        days=random.randint(0, 365)
    )
    
    distance_km = round(random.uniform(0.5, 20.0), 2)
    
    duration_minutes = round(distance_km * random.uniform(2, 5), 1)

    end_time = start_time + timedelta(minutes=duration_minutes)
    
    status = "Unvalidated"
    
    current_ride=[
        ride_id,
        bike_id,
        user_type,      
        start_station,
        end_station,
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S"),
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

create_dataset("data/bike_rides.csv", 100)