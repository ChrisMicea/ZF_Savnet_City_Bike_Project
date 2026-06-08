import validator
import cleaner
import analyzer

def main():
    validator.validate_records("data/bike_rides.csv")
    cleaned_data = cleaner.clean_data("data/bike_rides.csv", "data/bike_rides_cleaned.csv")
    print(analyzer.analyze(cleaned_data))

    # rides by hour nu merge
if __name__ == "__main__":
    main()
