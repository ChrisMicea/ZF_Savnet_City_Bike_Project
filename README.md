# ZF Savnet City Bike Project

A City Bike Anomaly Hunter that reads messy city bike-sharing ride data from a CSV file, validates each record, cleans what can safely be cleaned, detects suspicious rides and operational anomalies, analyzes usage patterns, and generates a readable report for a City Mobility Operations Analyst.

## Features

- **Data Validation**: Validates bike ride records against business rules (timestamps, station names, user types, distances, durations)
- **Data Cleaning**: Automatically fixes common data issues while flagging suspicious records
- **Anomaly Detection**: Detects operational anomalies including bike overlaps, station spikes, route anomalies, and duplicate records
- **Usage Analytics**: Analyzes ride patterns by user type, station, day of week, and hour
- **Report Generation**: Generates text reports and PDF reports with visualizations

## Prerequisites

- Python 3.14+
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ZF_Savnet_City_Bike_Project
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Main Program

To process bike ride data and generate reports:

```bash
python src/main.py
```

This will:
- Read data from `data/bike_rides.csv`
- Validate and clean the data
- Detect anomalies
- Generate reports in the `reports/` directory:
  - `bike_ride_quality_report.txt` - Detailed quality report
  - `anomaly_report.txt` - Anomaly detection results
  - `bike_ride_report.pdf` - PDF report with visualizations

### Generating Test Data

To generate synthetic test data:

```bash
python src/data_generator.py
```

This creates `data/bike_rides.csv` with 10,000 sample ride records.

### Running Tests

To run the test suite:

```bash
python tests/test_validator.py
python tests/test_cleaner.py
```

## Project Structure

```
ZF_Savnet_City_Bike_Project/
├── .venv/                 # Virtual environment (gitignored)
├── data/                  # Input data files (gitignored)
├── reports/               # Generated reports (gitignored)
├── src/
│   ├── main.py           # Main entry point
│   ├── validator.py      # Data validation logic
│   ├── cleaner.py        # Data cleaning logic
│   ├── analyzer.py       # Usage analytics
│   ├── anomaly_detector.py # Anomaly detection
│   ├── reporter.py       # Text report generation
│   ├── pdf_reporter.py   # PDF report generation
│   ├── data_generator.py # Test data generator
│   └── utils.py          # Shared utilities
├── tests/
│   ├── test_validator.py # Validator tests
│   └── test_cleaner.py   # Cleaner tests
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Implementation Details

### Data Validation (`validator.py`)

The validator enforces the following business rules:
- **Timestamps**: Start time must be before end time, both must be valid datetime strings
- **Stations**: Start and end stations must be from the predefined station list
- **User Types**: Must be one of: tourist, member, casual
- **Distances**: Must be non-negative and reasonable (< 50 km)
- **Durations**: Must be non-negative and reasonable (< 8 hours)

Records are categorized as:
- `clean`: Passes all validation rules
- `fixed`: Minor issues that can be auto-corrected
- `suspicious`: Fails validation but might be real data
- `beyond_repair`: Invalid data that cannot be salvaged

### Data Cleaning (`cleaner.py`)

The cleaner attempts to fix common issues:
- Trims whitespace from station names
- Normalizes user type casing
- Fixes obvious timestamp format issues
- Corrects negative distances/durations to zero

### Anomaly Detection (`anomaly_detector.py`)

Implements multiple anomaly detection rules:
1. **Bike Overlaps**: Detects bikes appearing in multiple rides simultaneously
2. **Station Spikes**: Identifies stations with unusual usage spikes (>3x average)
3. **Route Spikes**: Detects routes with abnormal frequency
4. **Zero Duration Rides**: Flags rides with 0-minute duration
5. **Duration/Timestamp Mismatches**: Detects inconsistent time calculations
6. **Distance/Duration Anomalies**: Identifies unrealistic speed patterns
7. **Suspicious Bikes**: Tracks bikes with frequent anomalies
8. **Suspicious Stations**: Tracks stations with frequent anomalies
9. **Duplicate Ride IDs**: Detects duplicate ride identifiers
10. **Unknown Stations**: Flags rides with unrecognized station names

### Analytics (`analyzer.py`)

Calculates usage statistics:
- Ride counts by user type
- Most popular start/end stations
- Top routes
- Most used bikes
- Average duration and distance
- Rides by day of week and hour
- busiest/quietest periods

### Report Generation

- **Text Reports** (`reporter.py`): Generates human-readable text summaries
- **PDF Reports** (`pdf_reporter.py`): Creates professional PDFs with charts and tables using ReportLab and Matplotlib

## Testing

The project includes unit tests for the validator and cleaner modules. Tests cover:
- Validation rule enforcement
- Edge cases and boundary conditions
- Data cleaning transformations
- Error handling
