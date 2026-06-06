PROBABILITY_RECORD_WILL_CONTAIN_SPACES=0.1
PROBABILITY_RECORD_WILL_LACK_BIKE_ID=0.1
PROBABILITY_RECORD_WILL_MISSING_STATIONS=0.1
PROBABILITY_RECORD_WILL_CONTAIN_INVALID_STATIONS=0.1
PROBABILITY_RECORD_WILL_CONTAIN_INVALID_FORMATING=0.1
PROBABILITY_RECORD_WILL_CONTAIN_INVALID_BIKE_IDS=0.1
PROBABILITY_RECORD_WILL_CONTAIN_INVALID_DURATION=0.1
PROBABILITY_RECORD_WILL_CONTAIN_INVALID_USER_TYPE=0.1

dict_stations = {'Central_Station': 1, 'Tech_District': 2, 'River_Park': 3, 'Downtown_Plaza': 4, 'East_Terminal': 5, 'West_End': 6, 'University': 7, 'South_Gardens': 8, 'City_Hall': 9, 'North_Market': 10}
valid_user_types = {"member", "casual", "tourist"}
accepted_date_formats = [
    "%Y/%d/%m %H:%M",   # Y/d/m
    "%Y-%m-%d %H:%M",   # normal (kept for mix)
    "%d-%m-%Y %H:%M",   # d-m-Y
    "%Y/%m/%d %H:%M",   # Y/m/d
    "%d/%m/%Y %H:%M",   # d/m/Y
]