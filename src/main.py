import validator
import cleaner
import analyzer
from anomaly_detector import analyze_anomalies

def main():
    validator.validate_records("data/bike_rides.csv")
    cleaned_data = cleaner.clean_data("data/bike_rides.csv", "data/bike_rides_cleaned.csv")
    results = analyze_anomalies()
    #generate_anomaly_report(results)
    print(analyzer.analyze(cleaned_data))
if __name__ == "__main__":
    main()
