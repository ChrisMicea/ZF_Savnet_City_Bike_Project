## Challenge Title

Bike Path Detective: The City Ride Anomaly Hunter

## Engineering Ticket

The City Mobility Operations team has a very urban mystery on its hands: their bike-sharing ride data is full of weird little gremlins.

Some bikes appear to teleport across town. Some rides have negative durations, which would be impressive if time travel were part of the subscription plan. A few trips last longer than a full workday. Station names are written five different ways. One bike seems to start a second ride before finishing the first one. The dashboard says everything is “probably fine,” but the Operations Manager is not convinced.

The team receives bike ride data from docking stations, mobile app checkouts, maintenance logs, and payment systems. Unfortunately, those systems do not always agree on formatting, timing, or reality.

Your end user is a City Mobility Operations Analyst who needs a reliable Python tool that can clean messy ride records, separate trustworthy records from suspicious ones, and turn thousands of bike trips into useful operational insights.

They need to answer questions like:

* Which stations are busiest?  
* Which routes are most popular?  
* Are any bikes producing impossible ride records?  
* Are some stations suddenly overloaded?  
* Are there patterns by day of week?  
* Which records should be excluded from reporting?

Your job is to turn messy mobility data into better city decisions. Because software is not valuable just because it runs. It is valuable when it helps real people understand what is happening and act with confidence.

## Your Mission

Build a Python 3.13 program that reads messy city bike-sharing ride data from a CSV file, validates each record, cleans what can safely be cleaned, detects suspicious rides and operational anomalies, analyzes usage patterns, and generates a readable report for a City Mobility Operations Analyst.

Your team must also create a mock data generator that produces a realistic dataset with at least 10,000 records, including both normal ride records and intentionally messy edge cases.

You may only use Python 3.13 builtins and the standard library.

No Pandas. No NumPy. No requests. No third-party packages. No mysterious “pip install and pray” energy.

This is Python Essentials, city-bike edition.

## End User

The primary end user is a City Mobility Operations Analyst working for a public bike-sharing program.

They need to make decisions such as:

* Which stations need more bikes during busy periods?  
* Which stations are often used as starting points or ending points?  
* Which routes are most popular?  
* Which bikes may have broken sensors or bad checkout records?  
* Which ride records should be excluded from official reports?  
* Whether unusual usage is caused by real demand, bad data, special events, or operational issues.  
* Which days of the week have the highest usage.

This tool helps the analyst spend less time manually fixing spreadsheets and more time making the bike-sharing system reliable for real riders.

In other words: fewer spreadsheet potholes, smoother city rides.

## Team Roles

### Data Guardian

Owns the data quality side of the project.

Responsibilities:

* Defines what a valid city bike ride record looks like.  
* Designs realistic messy records for the mock dataset.  
* Creates edge cases such as missing stations, invalid dates, duplicate ride IDs, impossible durations, and overlapping rides.  
* Helps decide which records should be cleaned, rejected, or flagged for review.  
* Makes sure the generated dataset contains realistic mess, not just random keyboard soup.  
* Tracks which data issues are formatting problems and which issues change the meaning of the ride.

### Logic Builder

Owns the core Python implementation.

Responsibilities:

* Builds functions for reading files, parsing records, validating fields, cleaning values, processing rides, and detecting anomalies.  
* Implements analysis logic such as ride counts, average duration, popular routes, busiest stations, and day-of-week patterns.  
* Implements overlap detection for bikes that appear to be in two rides at the same time.  
* Keeps the code organized into small, understandable functions.  
* Makes sure bad data is handled gracefully instead of crashing the program dramatically in front of everyone.

### Insight Storyteller

Owns the final user experience.

Responsibilities:

* Designs the final report format.  
* Makes sure the output is useful to a non-technical City Mobility Operations Analyst.  
* Explains what the data issues mean in plain language.  
* Connects technical findings to real operational value.  
* Leads the final presentation flow and demo.  
* Helps the team tell the story from messy ride records to better city decisions.

These are collaboration roles, not silos. Everyone should review the code, understand the logic, participate in testing, and be able to explain the full solution.

No “I only named the variables” escape hatch.

## Dataset

Use a CSV file for this challenge.

Why CSV?

* It is beginner-friendly.  
* It is easy to inspect manually.  
* It works well with Python’s built-in `csv` module.  
* It resembles real exports from city systems, station logs, and operations dashboards.  
* It keeps the focus on Python logic instead of file-format gymnastics.

Each record represents one bike-sharing ride.

Suggested fields:

```
ride_id,bike_id,start_station,end_station,start_time,end_time,duration_minutes,user_type,distance_km
```

The `start_time` and `end_time` fields should represent when the ride began and ended.

Recommended datetime format:

```
YYYY-MM-DD HH:MM
```

Example records:

```
ride_id,bike_id,start_station,end_station,start_time,end_time,duration_minutes,user_type,distance_km
RIDE-1001,BIKE-042,Central Park,Old Town,2026-04-12 08:15,2026-04-12 08:37,22,member,3.4
RIDE-1002 , bike-042 , central park , OLD TOWN ,2026/04/12 09:05,2026/04/12 09:29, 24 , Member , 3.6 km
RIDE-1003,BIKE-108,Riverside,Riverside,2026-04-12 10:00,2026-04-12 09:45,-15,tourist,0.2
RIDE-1004,BIKE-215,,University Gate,2026-04-13 14:10,2026-04-13 14:28,18,casual,2.1
RIDE-1001,BIKE-300,Airport Hub,Central Park,2026-04-14 17:30,2026-04-14 18:02,32,member,6.8
```

What these examples show:

* `RIDE-1001` is a clean valid ride.  
* `RIDE-1002` is messy but fixable: extra spaces, inconsistent casing, lowercase bike ID, different datetime separator, and distance written with `km`.  
* `RIDE-1003` is invalid or suspicious: negative duration, end time before start time, and a suspiciously tiny distance for a broken-looking ride.  
* `RIDE-1004` is invalid because the start station is missing.  
* The final `RIDE-1001` is a duplicate ride ID and should be flagged.

Your team must generate a mock dataset file with at least 10,000 records.

## Mock Data Generator Requirements

Create a Python script that generates your dataset using Python builtins only.

The generator should create a file such as:

```
data/generated_rides.csv
```

Your generated dataset must include realistic normal records and intentional messy records.

Include examples of:

* Clean ride records.  
    
* Duplicate ride IDs.  
    
* Missing `bike_id`.  
    
* Missing `start_station` or `end_station`.  
    
* Invalid station names.  
    
* Station names with inconsistent formatting, such as:  
    
  * `Central Park`  
  * `central park`  
  * `CENTRAL PARK`  
  * `central park`


* Bike IDs with inconsistent formatting, such as:  
    
  * `BIKE-042`  
  * `bike-042`  
  * `BIKE-042`


* Invalid bike IDs, such as:  
    
  * `B-42`  
  * `BIKE-XYZ`  
  * empty values


* Invalid or inconsistent date formats, such as:  
    
  * `2026-04-12 08:15`  
  * `2026/04/12 08:15`  
  * `12-04-2026 08:15`  
  * `not-a-date`


* Negative ride durations.  
    
* Zero-minute rides.  
    
* Extremely long rides, such as rides over 180 or 360 minutes.  
    
* End times before start times.  
    
* Duration values that disagree with the start and end timestamps.  
    
* Distance values formatted in different ways, such as:  
    
  * `3.4`  
  * `3.4 km`  
  * `3.4`


* Invalid distance values, such as:  
    
  * `-2.0`  
  * `far`  
  * empty values


* Unknown user types, such as:  
    
  * `vip`  
  * `robot`  
  * `maybe`


* Bikes with overlapping rides.  
    
* Stations with unusually high usage.  
    
* Routes that appear much more often than normal.  
    
* Very short rides with very large distances.  
    
* Very long rides with very tiny distances.

Do not manually write 10,000 rows. Your generator should create them programmatically.

Your generated data should be messy in a controlled way. Realistic chaos is useful. Pure nonsense is just a raccoon in a CSV file.

## Functional Requirements

Your program must:

1. Read city bike ride records from a CSV file.  
     
2. Validate each record using clear business rules.  
     
3. Clean or normalize fields where it is safe to do so.  
     
4. Separate records into at least three groups:  
     
   * valid cleaned records  
   * invalid records  
   * suspicious records that may still be usable but need review

   

5. Store cleaned data using Python structures such as lists, dictionaries, sets, and tuples.  
     
6. Detect duplicate ride IDs.  
     
7. Parse and normalize bike IDs.  
     
8. Parse and normalize station names.  
     
9. Parse and normalize start and end datetimes.  
     
10. Parse and normalize duration values.  
      
11. Parse and normalize distance values.  
      
12. Normalize user types.  
      
13. Detect bikes with overlapping ride records.  
      
14. Analyze usage patterns.  
      
15. Detect anomalies and interesting patterns.  
      
16. Produce a readable report for the end user.  
      
17. Avoid hard-coding final results.  
      
18. Handle bad data gracefully instead of crashing.  
      
19. Organize the solution into small functions instead of one giant script.  
      
20. Include unit tests for important business logic.

## Validation Rules

Define and implement validation rules for each ride.

### Required Fields

The following fields are required for all records:

* `ride_id`  
* `bike_id`  
* `start_station`  
* `end_station`  
* `start_time`  
* `end_time`  
* `duration_minutes`  
* `user_type`

The following field is recommended but may be treated as optional depending on your team’s rule:

* `distance_km`

If `distance_km` is missing, the record may still be valid, but it should not be used in distance-based analysis.

### Ride ID

Valid ride IDs should:

* Not be empty.  
* Follow a pattern such as `RIDE-1001`.  
* Be unique in the dataset.

Duplicate ride IDs should be flagged.

A duplicate ride ID should not be silently fixed. The system should report it because duplicate identifiers can corrupt reports.

### Bike ID

Valid bike IDs should:

* Not be empty.  
* Follow a pattern such as `BIKE-042`.  
* Be normalized to uppercase.  
* Keep leading zeros when present.

Examples:

* `bike-042` should become `BIKE-042`.  
* `BIKE-042` should become `BIKE-042`.  
* `B-42` should be invalid unless your team clearly defines and documents another accepted pattern.

### Stations

Valid station names should:

* Not be empty.  
* Contain readable text.  
* Be normalized consistently.

Examples:

* `central park` should become `Central Park`.  
* `CENTRAL PARK` should become `Central Park`.  
* `old town` should become `Old Town`.

Missing station names should be invalid.

Unknown station names may be treated as suspicious if your team creates a known list of stations.

Suggested station list:

```
Central Park
Old Town
University Gate
Riverside
Museum Square
City Hall
Airport Hub
North Station
South Station
Market Street
Library Corner
Stadium East
```

### Start Time and End Time

Ride timestamps should be parsed using Python builtins such as `datetime`.

Accepted formats may include:

* `YYYY-MM-DD HH:MM`  
* `YYYY/MM/DD HH:MM`

Dates that cannot be parsed should be invalid.

The end time must be after the start time.

If the end time is before the start time, the ride should be invalid.

Future dates should be suspicious or invalid depending on your team’s rule. Your team must explain the choice.

### Duration Minutes

Duration should:

* Be present.  
* Be convertible to a number.  
* Be greater than 0\.  
* Usually match the difference between `start_time` and `end_time`.

Suggested rules:

* Duration less than or equal to 0 is invalid.  
* Duration above 180 minutes is suspicious.  
* Duration above 360 minutes is invalid unless your team chooses a different rule and explains it.  
* If the recorded duration differs from the timestamp-calculated duration by more than 5 minutes, the ride should be suspicious.

Example:

```
start_time = 2026-04-12 08:15
end_time = 2026-04-12 08:37
duration_minutes = 22
```

This is consistent.

Example:

```
start_time = 2026-04-12 08:15
end_time = 2026-04-12 08:37
duration_minutes = 95
```

This should be suspicious because the recorded duration does not match the timestamps.

### User Type

Accepted user types:

* `member`  
* `casual`  
* `tourist`

User type should be normalized to lowercase.

Unknown values such as `vip`, `robot`, `admin`, `maybe`, or empty values should be invalid.

### Distance KM

Distance is optional but useful.

If present, distance should:

* Be convertible to a non-negative number.  
* Support common messy formats like `3.4`, `3.4 km`, and `3.4`.  
* Not be negative.

Suggested rules:

* Distance below `0` is invalid.  
* Distance equal to `0` may be valid for same-station rides, but suspicious if the duration is long.  
* Distance above `30 km` is suspicious for a city bike ride.  
* Distance above `60 km` is invalid unless your team documents a special rule.

## Cleaning Rules

Clean and normalize values where it is safe and reasonable.

Examples of safe cleaning:

* Trim extra spaces from all string fields.  
* Normalize `ride_id` to uppercase.  
* Normalize `bike_id` to uppercase.  
* Normalize station names to title case.  
* Convert `central park`, `Central Park`, and `CENTRAL PARK` into `Central Park`.  
* Normalize user type to lowercase.  
* Convert duration strings like `" 24 "` into integer `24`.  
* Convert distance strings like `"3.4 km"` into float `3.4`.  
* Parse accepted datetime formats into a consistent format such as `YYYY-MM-DD HH:MM`.  
* Store cleaned records in a consistent dictionary structure.  
* Track whether a record required cleaning.

Do not silently fix values that could change business meaning.

Do not silently fix:

* Missing required fields.  
* Duplicate ride IDs.  
* Negative durations.  
* Zero durations.  
* End times before start times.  
* Invalid dates.  
* Unknown user types.  
* Negative distances.  
* Bikes with overlapping rides.  
* Duration values that strongly disagree with timestamps.  
* Extremely long rides.  
* Impossible distance and duration combinations.

Those should be reported as invalid or suspicious.

A good rule of thumb: clean formatting problems, but report reality problems.

Whitespace is harmless. Time travel is not.

## Analysis Tasks

Your program should produce useful insights from the cleaned data.

### Beginner-Friendly Analysis Tasks

Your report should include:

* Total records read.  
* Count of valid records.  
* Count of invalid records.  
* Count of suspicious records.  
* Count of records that required cleaning.  
* Total number of rides by user type.  
* Total rides by start station.  
* Total rides by end station.  
* Most popular start station.  
* Most popular end station.  
* Most popular route.  
* Average ride duration.  
* Average ride distance, using only records with valid distance.  
* Number of rides by day of week.

### Slightly More Advanced Analysis Tasks

Your program should also attempt several of these:

* Top 5 most-used bikes.  
* Top 5 most popular routes.  
* Stations with unusually high start activity.  
* Stations with unusually high end activity.  
* Routes with unusually high usage.  
* Average duration by user type.  
* Average distance by user type.  
* Busiest day of week.  
* Busiest hour of day.  
* Bikes with the most suspicious records.  
* Stations involved in the most suspicious records.  
* Percentage of records excluded from clean reporting.  
* Difference between member and casual rider patterns.  
* Same-station rides, where start station equals end station.

Keep the analysis explainable. A city analyst should be able to understand how each number was produced.

## Anomaly Detection

Your program must detect suspicious patterns.

Implement at least five anomaly rules.

Suggested anomaly rules:

### 1\. Duplicate Ride ID

The same `ride_id` appears more than once.

Why it matters:

Duplicate IDs can cause double-counting, incorrect reports, and confusion when investigating a ride.

### 2\. Impossible Duration

A ride has duration less than or equal to `0`.

Why it matters:

A bike ride cannot last negative minutes. Unless your bike fleet has discovered quantum mechanics, this is bad data.

### 3\. Extremely Long Ride

A ride has duration above a chosen threshold, such as `180` minutes.

Why it matters:

This may indicate a lost bike, failed checkout, maintenance issue, or incorrect end time.

### 4\. Invalid Timestamp Order

The end time is before the start time.

Why it matters:

This record should not be trusted for operational analysis.

### 5\. Duration Mismatch

The recorded `duration_minutes` differs from the calculated difference between `start_time` and `end_time` by more than a chosen tolerance, such as `5` minutes.

Why it matters:

This may reveal system sync problems between station logs and app logs.

### 6\. Bike Overlap

The same bike has two rides whose time ranges overlap.

Example:

```
BIKE-042 ride A: 08:00 to 08:30
BIKE-042 ride B: 08:20 to 08:45
```

Why it matters:

One bike cannot be checked out by two riders at the same time. This may indicate duplicate records, station sync issues, or bad bike IDs.

### 7\. Suspicious Station Spike

A station has much higher usage than most stations.

Beginner-friendly approach:

* Calculate average rides per station.  
* Flag stations with more than 3 times the average usage.

Why it matters:

This could indicate a real event, such as a concert or sports match, or a data problem.

### 8\. Suspicious Route Spike

A route appears much more often than normal.

Beginner-friendly approach:

* Count each `(start_station, end_station)` pair.  
* Flag routes with unusually high counts compared with other routes.

Why it matters:

This could show a popular commute route, a special event, or repeated bad records.

### 9\. Strange Distance and Duration Combination

Examples:

* Ride distance is above `20 km` but duration is under `5 minutes`.  
* Ride distance is below `0.2 km` but duration is above `120 minutes`.

Why it matters:

The numbers may be individually valid but suspicious together.

### 10\. Unknown Station Pattern

A station name does not match the known station list after cleaning.

Why it matters:

This may reveal typo problems, renamed stations, or bad exports.

Keep your rules explainable. The Operations Analyst should understand why a ride was flagged.

Avoid mysterious “algorithm says suspicious” logic. This is Python Essentials, not a fog machine with a keyboard.

## Report Output

Your program should print a readable report to the terminal and/or write it to a text file such as:

```
reports/bike_ride_quality_report.txt
```

The exact format is up to your team, but it should be understandable to a non-technical user.

Example structure:

```
City Bike Ride Quality Report
=============================

Dataset Summary
---------------
Total records read: 10,250
Valid cleaned records: 9,431
Invalid records: 512
Suspicious records: 307
Records requiring cleaning: 2,106

Ride Summary
------------
Total usable rides: 9,431
Member rides: 5,804
Casual rides: 2,891
Tourist rides: 736

Duration Summary
----------------
Average ride duration: 24.7 minutes
Rides above 180 minutes: 42
Invalid zero or negative durations: 31
Duration mismatches: 88

Station Summary
---------------
Most common start station: Central Park
Most common end station: Old Town
Busiest station overall: Central Park
Stations with unusual usage spikes: 2

Popular Routes
--------------
1. Central Park -> Old Town: 812 rides
2. University Gate -> City Hall: 641 rides
3. Riverside -> Museum Square: 598 rides

Day-of-Week Pattern
-------------------
Busiest day: Saturday
Quietest day: Monday

Bike Anomalies
--------------
Duplicate ride IDs: 19
Bikes with overlapping rides: 7
Bike with most suspicious records: BIKE-042

Data Quality Issues
-------------------
Missing stations: 73
Invalid dates: 44
Unknown user types: 28
Invalid distance values: 61

Recommended Follow-Up
---------------------
- Review bikes with overlapping rides for station sync problems.
- Investigate stations with sudden usage spikes.
- Exclude invalid duration records from official usage reporting.
- Check whether high-usage routes match known city events or commute patterns.
```

Your report should not just dump raw data. It should summarize what matters.

The best report feels like a helpful analyst wrote it, not like a dictionary fell down the stairs.

## Unit Testing Requirements

Unit tests are mandatory.

Use Python’s built-in `unittest` module.

Your tests should focus on business logic, not just whether files exist. Unit tests are not only for grades. They are a way to track edge cases, prevent regressions, and build confidence when your data gets weird.

Test ideas:

1. A clean ride record passes validation.  
2. A messy bike ID like `" bike-042 "` normalizes to `"BIKE-042"`.  
3. Station names like `" central park "` and `"CENTRAL PARK"` normalize to the same value.  
4. A ride with missing `start_station` is invalid.  
5. A ride with end time before start time is invalid.  
6. A duration of `0` or `-15` is rejected.  
7. A duplicate `ride_id` is detected.  
8. A bike with overlapping ride times is flagged as suspicious.  
9. A distance string like `"3.4 km"` is cleaned into `3.4`.  
10. An unknown user type like `"robot"` is invalid.  
11. A recorded duration that differs from timestamp duration by more than the allowed tolerance is suspicious.  
12. Summary calculations, such as average ride duration and most popular route, work on a small controlled dataset.

You do not need to test every line of code. Focus on the rules that protect the correctness of the program.

Good tests are tiny bike helmets for your functions. Wear them.

## Suggested Project Structure

```
project/
  data/
    sample_rides.csv
    generated_rides.csv
  reports/
    bike_ride_quality_report.txt
  src/
    main.py
    data_generator.py
    reader.py
    validator.py
    cleaner.py
    analyzer.py
    anomaly_detector.py
    reporter.py
  tests/
    test_validator.py
    test_cleaner.py
    test_analyzer.py
    test_anomaly_detector.py
  README.md
```

Suggested responsibilities:

* `data_generator.py`: creates the 10,000+ record mock dataset.  
* `reader.py`: reads CSV records safely.  
* `validator.py`: checks whether records follow the rules.  
* `cleaner.py`: normalizes fixable messy values.  
* `analyzer.py`: calculates summaries and insights.  
* `anomaly_detector.py`: detects suspicious patterns.  
* `reporter.py`: formats the final report.  
* `main.py`: connects everything together.  
* `tests/`: contains unit tests for the business logic.  
* `README.md`: explains how to run the generator, run the program, run tests, and understand the report.

## How to Use AI Like a Modern Engineer

You are encouraged to use tools like ChatGPT, Cursor, Windsurf, or VS Code Copilot.

But AI should help you think, not replace your thinking.

Use AI as a pair programmer, not as a homework machine.

Helpful ways to use AI:

* Ask AI to explain concepts you do not understand.  
* Ask AI to review your code for bugs or readability.  
* Ask AI to generate edge case ideas.  
* Ask AI to help write unit test scenarios.  
* Ask AI to compare two possible data structures.  
* Ask AI to explain an error message.  
* Ask AI to suggest how to break a big function into smaller functions.  
* Ask AI to help you make your final report clearer for a non-technical user.

Important rules:

* Do not blindly paste AI-generated code.  
* You must be able to explain every function in your project.  
* You are responsible for checking whether AI suggestions are correct.  
* AI can suggest tests, but your team must understand what each test proves.  
* AI can help with debugging, but you should still read the error message yourself.  
* AI is very good at sounding confident. It is not always very good at being correct. Politely fact-check the robot.

Example prompts you can ask an AI assistant:

1. “Here is my validation function for bike ride records. Can you review it for edge cases I missed?”  
2. “Can you explain how Python’s built-in `csv.DictReader` handles missing columns?”  
3. “What are good unit test cases for detecting overlapping bike rides?”  
4. “I have a list of cleaned ride dictionaries. What is a beginner-friendly way to count the most popular routes?”  
5. “Can you compare using a list of dictionaries versus a dictionary keyed by ride ID for this project?”  
6. “Here is my error message from `datetime.strptime`. Explain what it means and where I should look first.”  
7. “Can you suggest anomaly detection rules for bike-sharing data that are easy to implement with Python builtins?”  
8. “Can you help me refactor this long function into smaller functions without changing the behavior?”

Use AI to learn faster, review better, and think more clearly.

Do not use AI to avoid understanding your own project. During the final presentation, the robot will not be standing next to you wearing a team hoodie.

## Final Presentation

At the end, your team must present the project.

Your presentation should include:

1. The actual challenge you solved.  
2. Who the end user is.  
3. What problem the end user has.  
4. Why this problem matters.  
5. A short demo of your program.  
6. What data issues you found.  
7. What technical challenges you had during implementation.  
8. How you tested the business logic.  
9. What insights or anomalies your solution discovered.  
10. An estimate of how much value the solution could bring to the end user.

Think empathetically.

Do not only say:

```
“Our script works.”
```

Explain why it matters:

```
“Our tool helps a City Mobility Operations Analyst identify unreliable ride records, spot bikes with impossible usage patterns, find overloaded stations, and make better decisions about where bikes are needed most.”
```

Your final demo should show the journey from messy records to useful decisions.

The best projects will feel like small professional tools, not just Python exercises wearing a reflective safety vest.  
