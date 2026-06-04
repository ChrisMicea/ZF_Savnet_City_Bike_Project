import csv
import random
from datetime import datetime, timedelta
import utils

def generate_ride(ride_id):
    #Random messiness
    start_station = random.choice(list(utils.dict_stations.keys()))
    end_station = random.choice(list(utils.dict_stations.keys()))

    distance_km = round(random.uniform(0.5, 20.0), 2)

    duration_minutes = round(distance_km * random.uniform(2, 5), 1)

    start_time = datetime.now() - timedelta(
        days=random.randint(0, 365)
    )
    bike_id = f"Bike-{random.randint(1, 5000)}"
    end_time = start_time + timedelta(minutes=duration_minutes)
    user_type = random.choice(["Member", "Casual","Tourist","VIP","Robot","Admin",""])
    ride_id=f"RIDE-{random.randint(1,10000)}"

    current_ride=[
        ride_id,
        bike_id,      
        start_station,
        end_station,
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S"),
        distance_km,
        duration_minutes,
        user_type
    ]
    # Messiness Starter

    if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_SPACES: #only 10% of rides will have spaces
        current_ride = introduce_spaces(current_ride)
    if random.random() < utils.PROBABILITY_RECORD_WILL_LACK_BIKE_ID: #only 10% of rides will lack bike_id
        current_ride[1] = ""
    if random.random() < utils.PROBABILITY_RECORD_WILL_MISSING_STATIONS: #only 10% of rides will have missing Start station
        current_ride[2] = ""
    if random.random() < utils.PROBABILITY_RECORD_WILL_MISSING_STATIONS: #only 10% of rides will have missing End station
        current_ride[3] = ""

    return current_ride

def introduce_spaces(ride):
    for i, field in enumerate(ride):
        field=str(field)
        for j in range(len(field)):
            if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_SPACES:  # 10% chance to add a space
                field = field[:j] + ' ' + field[j:]
        ride[i] = field
    return ride

def create_invalid_station_names():
    for i,field in enumerate(ride):
        field=str(field)
        for j in range(len(field)):
            if random.random() < utils.PROBABILITY_RECORD_WILL_CONTAIN_LETTERS:  # 10% chance to add a letter
                field = field[:j] + random.choice(string.ascii_letters) + field[j:]
        ride[i] = field
    return ride


def create_dataset(filename, num_rows):
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "ride_id",
            "bike_id",
            "start_station",
            "end_station",
            "start_time",
            "end_time",
            "distance_km",
            "duration_minutes",
            "user_type"
        ])

        for ride_id in range(1, num_rows + 1):
            writer.writerow(generate_ride(ride_id))

create_dataset("data/bike_rides.csv", 100)