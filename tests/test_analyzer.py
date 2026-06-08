"""
test_analyzer.py
================
Unit tests for analyzer.py business logic.

Run from the project root with:
    python -m pytest tests/test_analyzer.py -v
  or:
    python -m unittest tests.test_analyzer -v

Each TestCase class tests one analyzer function in isolation.
"""

import unittest
import sys
import os

# Make sure Python can find analyzer.py and utils.py when the test file lives in a tests/ subfolder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

import analyzer
import utils


class TestUsable(unittest.TestCase):

    def test_filters_clean_records(self):
        """Only clean records should be included in usable list."""
        records = [
            {"status": "clean", "ride_id": "RIDE-1"},
            {"status": "fixed", "ride_id": "RIDE-2"},
            {"status": "suspicious", "ride_id": "RIDE-3"},
            {"status": "beyond_repair", "ride_id": "RIDE-4"},
        ]
        result = analyzer._usable(records)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(r["status"] in utils.ANALYSIS_STATUSES for r in result))

    def test_filters_fixed_records(self):
        """Fixed records should be included in usable list."""
        records = [
            {"status": "fixed", "ride_id": "RIDE-1"},
            {"status": "beyond_repair", "ride_id": "RIDE-2"},
        ]
        result = analyzer._usable(records)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "fixed")

    def test_filters_suspicious_records(self):
        """Suspicious records should be included in usable list."""
        records = [
            {"status": "suspicious", "ride_id": "RIDE-1"},
            {"status": "beyond_repair", "ride_id": "RIDE-2"},
        ]
        result = analyzer._usable(records)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "suspicious")

    def test_excludes_beyond_repair(self):
        """Beyond repair records should be excluded from usable list."""
        records = [
            {"status": "clean", "ride_id": "RIDE-1"},
            {"status": "beyond_repair", "ride_id": "RIDE-2"},
            {"status": "beyond_repair", "ride_id": "RIDE-3"},
        ]
        result = analyzer._usable(records)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "clean")

    def test_handles_empty_list(self):
        """Empty input should return empty list."""
        result = analyzer._usable([])
        self.assertEqual(result, [])

    def test_handles_missing_status(self):
        """Records without status should be treated as beyond_repair."""
        records = [
            {"ride_id": "RIDE-1"},
            {"status": "clean", "ride_id": "RIDE-2"},
        ]
        result = analyzer._usable(records)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "clean")


class TestDt(unittest.TestCase):

    def test_parses_valid_datetime(self):
        """Valid datetime should be parsed correctly."""
        record = {"start_time": "2026-04-12 08:15"}
        result = analyzer._dt(record, "start_time")
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.day, 12)
        self.assertEqual(result.hour, 8)
        self.assertEqual(result.minute, 15)

    def test_parses_end_time(self):
        """Should work with any datetime key."""
        record = {"end_time": "2026-04-12 08:37"}
        result = analyzer._dt(record, "end_time")
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.day, 12)


class TestAvg(unittest.TestCase):

    def test_calculates_average(self):
        """Should calculate average of numeric values."""
        values = [10, 20, 30]
        result = analyzer._avg(values)
        self.assertEqual(result, 20.0)

    def test_rounds_to_two_decimals(self):
        """Should round to two decimal places."""
        values = [1, 2, 3]
        result = analyzer._avg(values)
        self.assertEqual(result, 2.0)

    def test_handles_floats(self):
        """Should handle float values."""
        values = [1.5, 2.5, 3.0]
        result = analyzer._avg(values)
        self.assertEqual(result, 2.33)

    def test_returns_none_for_empty_list(self):
        """Empty list should return None."""
        result = analyzer._avg([])
        self.assertIsNone(result)


class TestTop(unittest.TestCase):

    def test_returns_most_common(self):
        """Should return most common items."""
        from collections import Counter
        counter = Counter(["a", "a", "b", "c", "c", "c"])
        result = analyzer._top(counter, 2)
        self.assertEqual(result, [("c", 3), ("a", 2)])

    def test_default_n_is_five(self):
        """Default n should be 5."""
        from collections import Counter
        counter = Counter(["a", "b", "c"])
        result = analyzer._top(counter)
        self.assertEqual(len(result), 3)

    def test_handles_empty_counter(self):
        """Empty counter should return empty list."""
        from collections import Counter
        counter = Counter()
        result = analyzer._top(counter)
        self.assertEqual(result, [])


class TestCountByStatus(unittest.TestCase):

    def test_counts_all_statuses(self):
        """Should count records by status."""
        records = [
            {"status": "clean"},
            {"status": "clean"},
            {"status": "fixed"},
            {"status": "suspicious"},
            {"status": "beyond_repair"},
        ]
        result = analyzer.count_by_status(records)
        self.assertEqual(result["total"], 5)
        self.assertEqual(result["clean"], 2)
        self.assertEqual(result["fixed"], 1)
        self.assertEqual(result["suspicious"], 1)
        self.assertEqual(result["beyond_repair"], 1)

    def test_calculates_excluded_percentage(self):
        """Should calculate percentage of beyond_repair records."""
        records = [
            {"status": "clean"},
            {"status": "clean"},
            {"status": "beyond_repair"},
        ]
        result = analyzer.count_by_status(records)
        self.assertEqual(result["excluded_percentage"], 33.3)

    def test_handles_empty_list(self):
        """Empty list should return zero counts."""
        result = analyzer.count_by_status([])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["clean"], 0)
        self.assertEqual(result["excluded_percentage"], 0.0)

    def test_handles_missing_status(self):
        """Missing status should be counted as beyond_repair."""
        records = [
            {"ride_id": "RIDE-1"},
            {"status": "clean"},
        ]
        result = analyzer.count_by_status(records)
        self.assertEqual(result["beyond_repair"], 1)


class TestRidesByUserType(unittest.TestCase):

    def test_counts_by_user_type(self):
        """Should count rides by user type."""
        usable = [
            {"user_type": "member"},
            {"user_type": "member"},
            {"user_type": "casual"},
            {"user_type": "tourist"},
        ]
        result = analyzer.rides_by_user_type(usable)
        self.assertEqual(result["member"], 2)
        self.assertEqual(result["casual"], 1)
        self.assertEqual(result["tourist"], 1)

    def test_handles_empty_list(self):
        """Empty list should return empty counter."""
        result = analyzer.rides_by_user_type([])
        self.assertEqual(len(result), 0)


class TestRidesByStation(unittest.TestCase):

    def test_counts_by_start_station(self):
        """Should count rides by start station."""
        usable = [
            {"start_station": "Central_Station"},
            {"start_station": "Central_Station"},
            {"start_station": "City_Hall"},
        ]
        result = analyzer.rides_by_station(usable, "start_station")
        self.assertEqual(result["Central_Station"], 2)
        self.assertEqual(result["City_Hall"], 1)

    def test_counts_by_end_station(self):
        """Should count rides by end station."""
        usable = [
            {"end_station": "City_Hall"},
            {"end_station": "City_Hall"},
            {"end_station": "Central_Station"},
        ]
        result = analyzer.rides_by_station(usable, "end_station")
        self.assertEqual(result["City_Hall"], 2)
        self.assertEqual(result["Central_Station"], 1)

    def test_ignores_missing_station(self):
        """Records without station should be ignored."""
        usable = [
            {"start_station": "Central_Station"},
            {"ride_id": "RIDE-1"},
        ]
        result = analyzer.rides_by_station(usable, "start_station")
        self.assertEqual(result["Central_Station"], 1)
        self.assertEqual(len(result), 1)


class TestRidesByRoute(unittest.TestCase):

    def test_counts_by_route(self):
        """Should count rides by route (start, end) tuple."""
        usable = [
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "City_Hall", "end_station": "Central_Station"},
        ]
        result = analyzer.rides_by_route(usable)
        self.assertEqual(result[("Central_Station", "City_Hall")], 2)
        self.assertEqual(result[("City_Hall", "Central_Station")], 1)

    def test_ignores_missing_stations(self):
        """Records without start or end station should be ignored."""
        usable = [
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "Central_Station"},
            {"end_station": "City_Hall"},
        ]
        result = analyzer.rides_by_route(usable)
        self.assertEqual(result[("Central_Station", "City_Hall")], 1)
        self.assertEqual(len(result), 1)


class TestRidesByBike(unittest.TestCase):

    def test_counts_by_bike_id(self):
        """Should count rides by bike ID."""
        usable = [
            {"bike_id": "BIKE-0420"},
            {"bike_id": "BIKE-0420"},
            {"bike_id": "BIKE-0421"},
        ]
        result = analyzer.rides_by_bike(usable)
        self.assertEqual(result["BIKE-0420"], 2)
        self.assertEqual(result["BIKE-0421"], 1)

    def test_ignores_missing_bike_id(self):
        """Records without bike_id should be ignored."""
        usable = [
            {"bike_id": "BIKE-0420"},
            {"ride_id": "RIDE-1"},
        ]
        result = analyzer.rides_by_bike(usable)
        self.assertEqual(result["BIKE-0420"], 1)
        self.assertEqual(len(result), 1)


class TestAvgDuration(unittest.TestCase):

    def test_calculates_average_duration(self):
        """Should calculate average duration in minutes."""
        usable = [
            {"duration_minutes": "10"},
            {"duration_minutes": "20"},
            {"duration_minutes": "30"},
        ]
        result = analyzer.avg_duration(usable)
        self.assertEqual(result, 20.0)

    def test_returns_none_for_empty_list(self):
        """Empty list should return None."""
        result = analyzer.avg_duration([])
        self.assertIsNone(result)

    def test_ignores_missing_duration(self):
        """Records without duration should be ignored."""
        usable = [
            {"duration_minutes": "10"},
            {"ride_id": "RIDE-1"},
        ]
        result = analyzer.avg_duration(usable)
        self.assertEqual(result, 10.0)


class TestAvgDistance(unittest.TestCase):

    def test_calculates_average_distance(self):
        """Should calculate average distance in km."""
        usable = [
            {"distance_km": "1.0"},
            {"distance_km": "2.0"},
            {"distance_km": "3.0"},
        ]
        result = analyzer.avg_distance(usable)
        self.assertEqual(result, 2.0)

    def test_returns_none_for_empty_list(self):
        """Empty list should return None."""
        result = analyzer.avg_distance([])
        self.assertIsNone(result)

    def test_ignores_missing_distance(self):
        """Records without distance should be ignored."""
        usable = [
            {"distance_km": "1.0"},
            {"ride_id": "RIDE-1"},
        ]
        result = analyzer.avg_distance(usable)
        self.assertEqual(result, 1.0)


class TestAvgByUserType(unittest.TestCase):

    def test_calculates_avg_by_user_type(self):
        """Should calculate average by user type for a field."""
        usable = [
            {"user_type": "member", "duration_minutes": "10"},
            {"user_type": "member", "duration_minutes": "20"},
            {"user_type": "casual", "duration_minutes": "30"},
        ]
        result = analyzer.avg_by_user_type(usable, "duration_minutes")
        self.assertEqual(result["member"], 15.0)
        self.assertEqual(result["casual"], 30.0)

    def test_works_with_distance(self):
        """Should work with distance_km field."""
        usable = [
            {"user_type": "member", "distance_km": "5.0"},
            {"user_type": "member", "distance_km": "10.0"},
            {"user_type": "casual", "distance_km": "3.0"},
        ]
        result = analyzer.avg_by_user_type(usable, "distance_km")
        self.assertEqual(result["member"], 7.5)
        self.assertEqual(result["casual"], 3.0)

    def test_ignores_missing_user_type(self):
        """Records without user_type should be ignored."""
        usable = [
            {"user_type": "member", "duration_minutes": "10"},
            {"duration_minutes": "20"},
        ]
        result = analyzer.avg_by_user_type(usable, "duration_minutes")
        self.assertEqual(result["member"], 10.0)
        self.assertEqual(len(result), 1)

    def test_ignores_missing_field(self):
        """Records without the specified field should be ignored."""
        usable = [
            {"user_type": "member", "duration_minutes": "10"},
            {"user_type": "member"},
        ]
        result = analyzer.avg_by_user_type(usable, "duration_minutes")
        self.assertEqual(result["member"], 10.0)


class TestRidesByDay(unittest.TestCase):

    def test_counts_by_day_of_week(self):
        """Should count rides by day of week."""
        usable = [
            {"start_time": "2026-04-06 08:15"},  # Monday
            {"start_time": "2026-04-06 10:15"},  # Monday
            {"start_time": "2026-04-07 08:15"},  # Tuesday
        ]
        result = analyzer.rides_by_day(usable)
        self.assertEqual(result["Monday"], 2)
        self.assertEqual(result["Tuesday"], 1)
        self.assertEqual(result["Wednesday"], 0)

    def test_includes_all_days(self):
        """Should include all 7 days in result."""
        usable = [{"start_time": "2026-04-06 08:15"}]
        result = analyzer.rides_by_day(usable)
        self.assertEqual(len(result), 7)
        self.assertIn("Monday", result)
        self.assertIn("Tuesday", result)
        self.assertIn("Wednesday", result)
        self.assertIn("Thursday", result)
        self.assertIn("Friday", result)
        self.assertIn("Saturday", result)
        self.assertIn("Sunday", result)

    def test_ignores_missing_start_time(self):
        """Records without start_time should be ignored."""
        usable = [
            {"start_time": "2026-04-06 08:15"},
            {"ride_id": "RIDE-1"},
        ]
        result = analyzer.rides_by_day(usable)
        self.assertEqual(result["Monday"], 1)


class TestRidesByHour(unittest.TestCase):

    def test_counts_by_hour(self):
        """Should count rides by hour of day."""
        usable = [
            {"start_time": "2026-04-06 08:15"},
            {"start_time": "2026-04-06 08:30"},
            {"start_time": "2026-04-06 10:15"},
        ]
        result = analyzer.rides_by_hour(usable)
        self.assertEqual(result[8], 2)
        self.assertEqual(result[10], 1)

    def test_includes_all_hours(self):
        """Should include all 24 hours in result."""
        usable = [{"start_time": "2026-04-06 08:15"}]
        result = analyzer.rides_by_hour(usable)
        self.assertEqual(len(result), 24)
        for hour in range(24):
            self.assertIn(hour, result)

    def test_ignores_missing_start_time(self):
        """Records without start_time should be ignored."""
        usable = [
            {"start_time": "2026-04-06 08:15"},
            {"ride_id": "RIDE-1"},
        ]
        result = analyzer.rides_by_hour(usable)
        self.assertEqual(result[8], 1)


class TestSuspiciousByBike(unittest.TestCase):

    def test_counts_suspicious_by_bike(self):
        """Should count suspicious records by bike ID."""
        records = [
            {"status": "suspicious", "bike_id": "BIKE-0420"},
            {"status": "suspicious", "bike_id": "BIKE-0420"},
            {"status": "clean", "bike_id": "BIKE-0420"},
            {"status": "suspicious", "bike_id": "BIKE-0421"},
        ]
        result = analyzer.suspicious_by_bike(records)
        self.assertEqual(result["BIKE-0420"], 2)
        self.assertEqual(result["BIKE-0421"], 1)

    def test_ignores_non_suspicious(self):
        """Non-suspicious records should be ignored."""
        records = [
            {"status": "clean", "bike_id": "BIKE-0420"},
            {"status": "fixed", "bike_id": "BIKE-0420"},
            {"status": "beyond_repair", "bike_id": "BIKE-0420"},
        ]
        result = analyzer.suspicious_by_bike(records)
        self.assertEqual(len(result), 0)

    def test_ignores_missing_bike_id(self):
        """Records without bike_id should be ignored."""
        records = [
            {"status": "suspicious", "bike_id": "BIKE-0420"},
            {"status": "suspicious"},
        ]
        result = analyzer.suspicious_by_bike(records)
        self.assertEqual(result["BIKE-0420"], 1)


class TestSuspiciousByStation(unittest.TestCase):

    def test_counts_suspicious_by_station(self):
        """Should count suspicious records by station (both start and end)."""
        records = [
            {"status": "suspicious", "start_station": "Central_Station", "end_station": "City_Hall"},
            {"status": "suspicious", "start_station": "Central_Station", "end_station": "City_Hall"},
            {"status": "suspicious", "start_station": "City_Hall", "end_station": "Central_Station"},
        ]
        result = analyzer.suspicious_by_station(records)
        self.assertEqual(result["Central_Station"], 3)
        self.assertEqual(result["City_Hall"], 3)

    def test_ignores_non_suspicious(self):
        """Non-suspicious records should be ignored."""
        records = [
            {"status": "clean", "start_station": "Central_Station"},
            {"status": "fixed", "start_station": "Central_Station"},
        ]
        result = analyzer.suspicious_by_station(records)
        self.assertEqual(len(result), 0)

    def test_counts_start_and_end_separately(self):
        """Both start_station and end_station should be counted."""
        records = [
            {"status": "suspicious", "start_station": "Central_Station", "end_station": "City_Hall"},
        ]
        result = analyzer.suspicious_by_station(records)
        self.assertEqual(result["Central_Station"], 1)
        self.assertEqual(result["City_Hall"], 1)


class TestSameStationCount(unittest.TestCase):

    def test_counts_same_station_rides(self):
        """Should count rides where start and end station are the same."""
        usable = [
            {"start_station": "Central_Station", "end_station": "Central_Station"},
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "City_Hall", "end_station": "City_Hall"},
        ]
        result = analyzer.same_station_count(usable)
        self.assertEqual(result, 2)

    def test_ignores_missing_stations(self):
        """Records without start or end station should be ignored."""
        usable = [
            {"start_station": "Central_Station", "end_station": "Central_Station"},
            {"start_station": "Central_Station"},
            {"end_station": "Central_Station"},
        ]
        result = analyzer.same_station_count(usable)
        self.assertEqual(result, 1)

    def test_handles_empty_list(self):
        """Empty list should return 0."""
        result = analyzer.same_station_count([])
        self.assertEqual(result, 0)


class TestAnalyze(unittest.TestCase):

    def test_returns_complete_analysis(self):
        """Should return complete analysis dictionary."""
        records = [
            {
                "status": "clean",
                "ride_id": "RIDE-1",
                "bike_id": "BIKE-0420",
                "user_type": "member",
                "start_station": "Central_Station",
                "end_station": "City_Hall",
                "start_time": "2026-04-06 08:15",
                "end_time": "2026-04-06 08:37",
                "duration_minutes": "22",
                "distance_km": "3.4",
            },
            {
                "status": "clean",
                "ride_id": "RIDE-2",
                "bike_id": "BIKE-0421",
                "user_type": "casual",
                "start_station": "City_Hall",
                "end_station": "Central_Station",
                "start_time": "2026-04-06 10:15",
                "end_time": "2026-04-06 10:37",
                "duration_minutes": "22",
                "distance_km": "3.4",
            },
        ]
        result = analyzer.analyze(records)
        
        # Check that all expected keys are present
        self.assertIn("status_counts", result)
        self.assertIn("rides_by_user_type", result)
        self.assertIn("rides_by_start", result)
        self.assertIn("rides_by_end", result)
        self.assertIn("most_popular_start", result)
        self.assertIn("most_popular_end", result)
        self.assertIn("most_popular_route", result)
        self.assertIn("top_5_routes", result)
        self.assertIn("top_5_bikes", result)
        self.assertIn("avg_duration", result)
        self.assertIn("avg_distance", result)
        self.assertIn("avg_duration_by_type", result)
        self.assertIn("avg_distance_by_type", result)
        self.assertIn("rides_by_day", result)
        self.assertIn("rides_by_hour", result)
        self.assertIn("busiest_day", result)
        self.assertIn("quietest_day", result)
        self.assertIn("busiest_hour", result)
        self.assertIn("suspicious_bikes", result)
        self.assertIn("suspicious_stations", result)
        self.assertIn("same_station_count", result)

    def test_calculates_status_counts(self):
        """Should calculate status counts correctly."""
        records = [
            {
                "status": "clean",
                "ride_id": "RIDE-1",
                "bike_id": "BIKE-0420",
                "user_type": "member",
                "start_station": "Central_Station",
                "end_station": "City_Hall",
                "start_time": "2026-04-06 08:15",
                "end_time": "2026-04-06 08:37",
                "duration_minutes": "22",
                "distance_km": "3.4",
            },
            {
                "status": "fixed",
                "ride_id": "RIDE-2",
                "bike_id": "BIKE-0421",
                "user_type": "casual",
                "start_station": "City_Hall",
                "end_station": "Central_Station",
                "start_time": "2026-04-06 10:15",
                "end_time": "2026-04-06 10:37",
                "duration_minutes": "22",
                "distance_km": "3.4",
            },
            {
                "status": "suspicious",
                "ride_id": "RIDE-3",
                "bike_id": "BIKE-0422",
                "user_type": "tourist",
                "start_station": "Central_Station",
                "end_station": "City_Hall",
                "start_time": "2026-04-06 12:15",
                "end_time": "2026-04-06 12:37",
                "duration_minutes": "22",
                "distance_km": "3.4",
            },
            {
                "status": "beyond_repair",
                "ride_id": "RIDE-4",
            },
        ]
        result = analyzer.analyze(records)
        self.assertEqual(result["status_counts"]["total"], 4)
        self.assertEqual(result["status_counts"]["clean"], 1)
        self.assertEqual(result["status_counts"]["fixed"], 1)
        self.assertEqual(result["status_counts"]["suspicious"], 1)
        self.assertEqual(result["status_counts"]["beyond_repair"], 1)

    def test_identifies_most_popular_start(self):
        """Should identify most popular start station."""
        records = [
            {
                "status": "clean",
                "start_station": "Central_Station",
                "end_station": "City_Hall",
                "start_time": "2026-04-06 08:15",
                "duration_minutes": "22",
                "distance_km": "3.4",
                "user_type": "member",
                "bike_id": "BIKE-0420",
            },
            {
                "status": "clean",
                "start_station": "Central_Station",
                "end_station": "City_Hall",
                "start_time": "2026-04-06 10:15",
                "duration_minutes": "22",
                "distance_km": "3.4",
                "user_type": "member",
                "bike_id": "BIKE-0421",
            },
            {
                "status": "clean",
                "start_station": "City_Hall",
                "end_station": "Central_Station",
                "start_time": "2026-04-06 12:15",
                "duration_minutes": "22",
                "distance_km": "3.4",
                "user_type": "casual",
                "bike_id": "BIKE-0422",
            },
        ]
        result = analyzer.analyze(records)
        self.assertEqual(result["most_popular_start"], ("Central_Station", 2))

    def test_handles_empty_records(self):
        """Empty records should return valid analysis with zeros."""
        result = analyzer.analyze([])
        self.assertEqual(result["status_counts"]["total"], 0)
        self.assertIsNone(result["most_popular_start"])
        self.assertIsNone(result["most_popular_end"])
        self.assertIsNone(result["most_popular_route"])

    def test_calculates_averages(self):
        """Should calculate average duration and distance."""
        records = [
            {
                "status": "clean",
                "duration_minutes": "10",
                "distance_km": "1.0",
                "user_type": "member",
                "start_time": "2026-04-06 08:15",
            },
            {
                "status": "clean",
                "duration_minutes": "20",
                "distance_km": "2.0",
                "user_type": "member",
                "start_time": "2026-04-06 10:15",
            },
        ]
        result = analyzer.analyze(records)
        self.assertEqual(result["avg_duration"], 15.0)
        self.assertEqual(result["avg_distance"], 1.5)


if __name__ == "__main__":
    unittest.main()
