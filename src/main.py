import validator
import cleaner
import analyzer

def main():
    validator.validate_records("data/bike_rides.csv")
    cleaned_data = cleaner.clean_data("data/bike_rides.csv", "data/bike_rides_cleaned.csv")
    print(analyzer.analyze(cleaned_data))

    # rides by hour nu merge
    # station spikes e gol - nu stiu daca e de la dataset, la fel si route_spikes
if __name__ == "__main__":
    main()
