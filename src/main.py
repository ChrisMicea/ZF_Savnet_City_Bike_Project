import validator
import cleaner

def main():
    validator.validate_records("data/bike_rides.csv")
    cleaner.clean_data("data/bike_rides.csv", "data/bike_rides_cleaned.csv")
if __name__ == "__main__":
    main()
