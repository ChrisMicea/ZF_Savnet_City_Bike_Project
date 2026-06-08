import validator
import cleaner
import analyzer
import reporter
from anomaly_detector import analyze_anomalies

def main():
    validator.validate_records("data/bike_rides.csv")
    cleaned_data = cleaner.clean_data("data/bike_rides.csv", "data/bike_rides_cleaned.csv")
    anomalies = analyze_anomalies()
    analysis  = analyzer.analyze(cleaned_data)
    print(analysis)
    reporter.generate_reports(analysis, anomalies, quiet=True)


if __name__ == "__main__":
    main()
