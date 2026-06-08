import validator
import cleaner
from anomaly_detector import analyze_anomalies, generate_anomaly_report
from report import generate_report

def main():
    validator.validate_records("data/bike_rides.csv")
    cleaner.clean_data("data/bike_rides.csv", "data/bike_rides_cleaned.csv")
    results = analyze_anomalies()
    generate_anomaly_report(results)
    generate_report()
if __name__ == "__main__":
    main()
