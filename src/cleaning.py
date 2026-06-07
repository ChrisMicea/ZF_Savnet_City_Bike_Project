# cleaning and generating new csv file with cleaned data
import csv
import validator

def clean_data(input_file:"data/bike_rides.csv", output_file:"data/bike_rides_cleaned.csv"):
    with open(input_file, "r") as infile, open(output_file, "w") as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            # status = clean_ride_id(row)
            # status = clean_bike_id(row)
            # status = clean_user_type(row)
            # status = clean_station(row, 0)
            # clean_station(row, 1)
            # status = clean_start_time(row)
            # clean_end_time(row)
            # clean_duration(row)
            # status = clean_spaces(row)
            status = status_report(row)
            cleaned_row = {key: value.strip() if value else value for key, value in row.items()}
            writer.writerow(cleaned_row)



def clean_spaces(record: dict):
 # For every field except start_time and end_time, if it contains spaces, remove them
 
    for key, value in record.items():
        if key not in ["start_time", "end_time"] and " " in value:
            record[key] = value.replace(" ", "")
    return record

def clean_ride(record: dict):
    
    # If ride_id doesn't match the pattern, replace it with "RIDE-XXXXX"
    if not re.match(r"^RIDE-\d{5}$", record["ride_id"]):
        record["ride_id"] = "RIDE-" + "X" * 5
    # Make each ride_id unique by adding a counter
    record["ride_id"] = record["ride_id"] + "_" + str(hash(record["ride_id"]) % 10000)
    
    return record
def clean_bike_id(record: dict):
    # take all the validation fields and clean them accordingly for each field

    pass