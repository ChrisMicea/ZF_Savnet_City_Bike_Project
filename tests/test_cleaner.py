"""
test_cleaner.py
================
Unit tests for cleaner.py business logic.

Run from the project root with:
    python -m pytest tests/test_cleaner.py -v
  or:
    python -m unittest tests.test_cleaner -v

Each TestCase class tests one cleaner function in isolation.
"""

import unittest
import sys
import os

# Make sure Python can find cleaner.py and utils.py when the test file lives in a tests/ subfolder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

import cleaner
import utils


def _reset_cleaner_state():
    """
    cleaner.py keeps state in module-level sets/dicts:
    - _ride_ids_seen
    - _bike_intervals
    Call this before any test that touches these so tests don't bleed into each other.
    """
    cleaner._ride_ids_seen.clear()
    cleaner._bike_intervals.clear()


class TestCleanSpaces(unittest.TestCase):

    def test_removes_spaces_from_all_fields(self):
        """Spaces should be removed from all fields except start_time and end_time."""
        record = {
            "ride_id": "R I D E-1",
            "bike_id": "B I K E-1",
            "user_type": "m e m b e r",
            "start_station": "C e n t r a l",
            "end_station": "C i t y",
            "start_time": "2026-04-12 08:15",
            "end_time": "2026-04-12 08:37",
            "duration_minutes": "2 2",
            "distance_km": "3 . 4",
        }
        result = cleaner.clean_spaces(record)
        self.assertEqual(result["ride_id"], "RIDE-1")
        self.assertEqual(result["bike_id"], "BIKE-1")
        self.assertEqual(result["user_type"], "member")
        self.assertEqual(result["start_station"], "Central")
        self.assertEqual(result["end_station"], "City")
        self.assertEqual(result["start_time"], "2026-04-12 08:15")  # unchanged
        self.assertEqual(result["end_time"], "2026-04-12 08:37")  # unchanged
        self.assertEqual(result["duration_minutes"], "22")
        self.assertEqual(result["distance_km"], "3.4")

    def test_preserves_datetime_spaces(self):
        """start_time and end_time should keep their spaces."""
        record = {
            "start_time": "2026-04-12 08:15",
            "end_time": "2026-04-12 08:37",
        }
        result = cleaner.clean_spaces(record)
        self.assertEqual(result["start_time"], "2026-04-12 08:15")
        self.assertEqual(result["end_time"], "2026-04-12 08:37")

    def test_handles_empty_values(self):
        """Empty values should not cause errors."""
        record = {
            "ride_id": "",
            "bike_id": "BIKE-1",
        }
        result = cleaner.clean_spaces(record)
        self.assertEqual(result["ride_id"], "")
        self.assertEqual(result["bike_id"], "BIKE-1")


class TestCleanRideId(unittest.TestCase):

    def setUp(self):
        _reset_cleaner_state()

    def test_converts_to_uppercase(self):
        """ride_id should be converted to uppercase."""
        record = {"ride_id": "ride-10001"}
        result = cleaner.clean_ride_id(record)
        self.assertEqual(result["ride_id"], "RIDE-10001")

    def test_already_uppercase_unchanged(self):
        """Already uppercase ride_id should remain unchanged."""
        record = {"ride_id": "RIDE-10001"}
        result = cleaner.clean_ride_id(record)
        self.assertEqual(result["ride_id"], "RIDE-10001")

    def test_tracks_seen_ride_ids(self):
        """clean_ride_id should add ride_id to the seen set."""
        record = {"ride_id": "ride-10001"}
        cleaner.clean_ride_id(record)
        self.assertIn("RIDE-10001", cleaner._ride_ids_seen)


class TestCleanBikeId(unittest.TestCase):

    def test_normalizes_prefix_to_uppercase(self):
        """bike_id prefix should be converted to BIKE-."""
        record = {"bike_id": "bike-0420"}
        result = cleaner.clean_bike_id(record)
        self.assertEqual(result["bike_id"], "BIKE-0420")

    def test_mixed_case_prefix_normalized(self):
        """Mixed case bike_id should be normalized."""
        record = {"bike_id": "BiKe-0420"}
        result = cleaner.clean_bike_id(record)
        self.assertEqual(result["bike_id"], "BIKE-0420")

    def test_already_correct_format_unchanged(self):
        """Already correct BIKE- format should remain unchanged."""
        record = {"bike_id": "BIKE-0420"}
        result = cleaner.clean_bike_id(record)
        self.assertEqual(result["bike_id"], "BIKE-0420")


class TestCleanUserType(unittest.TestCase):

    def test_converts_to_lowercase(self):
        """user_type should be converted to lowercase."""
        record = {"user_type": "MEMBER"}
        result = cleaner.clean_user_type(record)
        self.assertEqual(result["user_type"], "member")

    def test_mixed_case_to_lowercase(self):
        """Mixed case user_type should be lowercased."""
        record = {"user_type": "MeMbEr"}
        result = cleaner.clean_user_type(record)
        self.assertEqual(result["user_type"], "member")

    def test_already_lowercase_unchanged(self):
        """Already lowercase user_type should remain unchanged."""
        record = {"user_type": "member"}
        result = cleaner.clean_user_type(record)
        self.assertEqual(result["user_type"], "member")


class TestCleanStation(unittest.TestCase):

    def test_converts_to_titlecase(self):
        """Station name should be converted to titlecase."""
        record = {"start_station": "central_station"}
        result = cleaner.clean_station(record, "start_station")
        self.assertEqual(result["start_station"], "Central_Station")

    def test_uppercase_to_titlecase(self):
        """Uppercase station should be converted to titlecase."""
        record = {"end_station": "CITY_HALL"}
        result = cleaner.clean_station(record, "end_station")
        self.assertEqual(result["end_station"], "City_Hall")

    def test_already_titlecase_unchanged(self):
        """Already titlecase station should remain unchanged."""
        record = {"start_station": "Central_Station"}
        result = cleaner.clean_station(record, "start_station")
        self.assertEqual(result["start_station"], "Central_Station")


class TestNormalizeDatetime(unittest.TestCase):

    def test_standard_format_normalized(self):
        """Standard YYYY-MM-DD HH:MM format should be preserved."""
        result = cleaner.normalize_datetime("2026-04-12 08:15")
        self.assertEqual(result, "2026-04-12 08:15")

    def test_slash_format_normalized(self):
        """YYYY/MM/DD HH:MM should be normalized to YYYY-MM-DD HH:MM."""
        result = cleaner.normalize_datetime("2026/04/12 08:15")
        self.assertEqual(result, "2026-12-04 08:15")

    def test_day_first_format_normalized(self):
        """DD-MM-YYYY HH:MM should be normalized to YYYY-MM-DD HH:MM."""
        result = cleaner.normalize_datetime("12-04-2026 08:15")
        self.assertEqual(result, "2026-04-12 08:15")

    def test_day_month_slash_format_normalized(self):
        """DD/MM/YYYY HH:MM should be normalized to YYYY-MM-DD HH:MM."""
        result = cleaner.normalize_datetime("12/04/2026 08:15")
        self.assertEqual(result, "2026-04-12 08:15")

    def test_year_day_month_format_normalized(self):
        """YYYY/d/m HH:MM should be normalized to YYYY-MM-DD HH:MM."""
        result = cleaner.normalize_datetime("2026/12/04 08:15")
        self.assertEqual(result, "2026-04-12 08:15")

    def test_invalid_format_returns_none(self):
        """Unparseable datetime should return None."""
        result = cleaner.normalize_datetime("not-a-date")
        self.assertIsNone(result)

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        result = cleaner.normalize_datetime("")
        self.assertIsNone(result)


class TestCleanTime(unittest.TestCase):

    def test_normalizes_start_time(self):
        """start_time should be normalized to standard format."""
        record = {"start_time": "2026/04/12 08:15"}
        result = cleaner.clean_time(record, 0)
        self.assertEqual(result["start_time"], "2026-12-04 08:15")

    def test_normalizes_end_time(self):
        """end_time should be normalized to standard format."""
        record = {"end_time": "2026/04/12 08:37"}
        result = cleaner.clean_time(record, 1)
        self.assertEqual(result["end_time"], "2026-12-04 08:37")

    def test_invalid_datetime_sets_none(self):
        """Invalid datetime should be set to None."""
        record = {"start_time": "invalid"}
        result = cleaner.clean_time(record, 0)
        self.assertIsNone(result["start_time"])


class TestCleanDuration(unittest.TestCase):

    def test_valid_duration_unchanged(self):
        """Valid positive duration should remain unchanged."""
        record = {"duration_minutes": "22", "status": "needs_cleaning"}
        result = cleaner.clean_duration(record)
        self.assertEqual(result["duration_minutes"], "22")
        self.assertEqual(result["status"], "needs_cleaning")

    def test_zero_duration_sets_suspicious(self):
        """Zero duration should set status to suspicious."""
        record = {"duration_minutes": "0", "status": "needs_cleaning"}
        result = cleaner.clean_duration(record)
        self.assertEqual(result["status"], "suspicious")

    def test_extremely_long_duration_sets_suspicious(self):
        """Duration exceeding MAX_RIDE_DURATION_MINUTES should set status to suspicious."""
        record = {"duration_minutes": "700", "status": "needs_cleaning"}
        result = cleaner.clean_duration(record)
        self.assertEqual(result["status"], "suspicious")

    def test_max_allowed_duration_unchanged(self):
        """Duration exactly at MAX_RIDE_DURATION_MINUTES should be accepted."""
        record = {"duration_minutes": "600", "status": "needs_cleaning"}
        result = cleaner.clean_duration(record)
        self.assertEqual(result["status"], "needs_cleaning")

    def test_float_duration_accepted(self):
        """Float duration should be accepted."""
        record = {"duration_minutes": "24.5", "status": "needs_cleaning"}
        result = cleaner.clean_duration(record)
        self.assertEqual(result["duration_minutes"], "24.5")
        self.assertEqual(result["status"], "needs_cleaning")


class TestCleanDistance(unittest.TestCase):

    def test_plain_distance_unchanged(self):
        """Plain numeric distance should remain unchanged."""
        record = {"distance_km": "3.4"}
        result = cleaner.clean_distance(record)
        self.assertEqual(result["distance_km"], "3.4")

    def test_removes_km_suffix_lowercase(self):
        """'km' suffix should be removed."""
        record = {"distance_km": "3.4 km"}
        result = cleaner.clean_distance(record)
        self.assertEqual(result["distance_km"], "3.4")

    def test_removes_km_suffix_uppercase(self):
        """'KM' suffix should be removed."""
        record = {"distance_km": "3.4KM"}
        result = cleaner.clean_distance(record)
        self.assertEqual(result["distance_km"], "3.4")

    def test_removes_km_suffix_mixed_case(self):
        """'Km' suffix should be removed."""
        record = {"distance_km": "3.4Km"}
        result = cleaner.clean_distance(record)
        self.assertEqual(result["distance_km"], "3.4")

    def test_strips_spaces(self):
        """Spaces around distance should be stripped."""
        record = {"distance_km": " 3.4 "}
        result = cleaner.clean_distance(record)
        self.assertEqual(result["distance_km"], "3.4")


class TestCheckCrossFields(unittest.TestCase):

    def setUp(self):
        _reset_cleaner_state()

    def test_end_time_before_start_time_sets_beyond_repair(self):
        """End time before start time should set status to beyond_repair."""
        record = {
            "start_time": "2026-04-12 08:37",
            "end_time": "2026-04-12 08:15",
            "duration_minutes": "22",
            "distance_km": "3.4",
            "bike_id": "BIKE-0420",
            "status": "needs_cleaning"
        }
        result = cleaner.check_cross_fields(record)
        self.assertEqual(result["status"], "beyond_repair")

    def test_duration_mismatch_sets_beyond_repair(self):
        """Duration that differs significantly from timestamp diff should set beyond_repair."""
        record = {
            "start_time": "2026-04-12 08:15",
            "end_time": "2026-04-12 08:37",  # 22 minutes
            "duration_minutes": "100",  # mismatch
            "distance_km": "3.4",
            "bike_id": "BIKE-0420",
            "status": "needs_cleaning"
        }
        result = cleaner.check_cross_fields(record)
        self.assertEqual(result["status"], "beyond_repair")

    def test_speed_too_slow_sets_suspicious(self):
        """Speed below MIN_SPEED_KPH should set suspicious."""
        record = {
            "start_time": "2026-04-12 08:15",
            "end_time": "2026-04-12 09:15",  # 60 minutes
            "duration_minutes": "60",
            "distance_km": "0.5",  # 0.5 km in 60 min = 0.5 kph (below 2.0)
            "bike_id": "BIKE-0420",
            "status": "needs_cleaning"
        }
        result = cleaner.check_cross_fields(record)
        self.assertEqual(result["status"], "suspicious")

    def test_speed_too_fast_sets_suspicious(self):
        """Speed above MAX_SPEED_KPH should set suspicious."""
        record = {
            "start_time": "2026-04-12 08:15",
            "end_time": "2026-04-12 08:37",  # 22 minutes
            "duration_minutes": "22",
            "distance_km": "50",  # 50 km in 22 min = 136 kph (above 60)
            "bike_id": "BIKE-0420",
            "status": "needs_cleaning"
        }
        result = cleaner.check_cross_fields(record)
        self.assertEqual(result["status"], "suspicious")

    def test_overlapping_rides_sets_suspicious(self):
        """Overlapping rides for the same bike should set suspicious."""
        bike_id = "BIKE-0420"
        
        # First ride
        record1 = {
            "start_time": "2026-04-12 08:00",
            "end_time": "2026-04-12 09:00",
            "duration_minutes": "60",
            "distance_km": "10",
            "bike_id": bike_id,
            "status": "needs_cleaning"
        }
        cleaner.check_cross_fields(record1)
        
        # Second overlapping ride
        record2 = {
            "start_time": "2026-04-12 08:30",
            "end_time": "2026-04-12 09:30",
            "duration_minutes": "60",
            "distance_km": "10",
            "bike_id": bike_id,
            "status": "needs_cleaning"
        }
        result = cleaner.check_cross_fields(record2)
        self.assertEqual(result["status"], "suspicious")

    def test_non_overlapping_rides_accepted(self):
        """Non-overlapping rides for the same bike should be accepted."""
        bike_id = "BIKE-0420"
        
        # First ride
        record1 = {
            "start_time": "2026-04-12 08:00",
            "end_time": "2026-04-12 09:00",
            "duration_minutes": "60",
            "distance_km": "10",
            "bike_id": bike_id,
            "status": "needs_cleaning"
        }
        cleaner.check_cross_fields(record1)
        
        # Second non-overlapping ride
        record2 = {
            "start_time": "2026-04-12 10:00",
            "end_time": "2026-04-12 11:00",
            "duration_minutes": "60",
            "distance_km": "10",
            "bike_id": bike_id,
            "status": "needs_cleaning"
        }
        result = cleaner.check_cross_fields(record2)
        self.assertEqual(result["status"], "needs_cleaning")

    def test_valid_cross_fields_unchanged(self):
        """Valid cross-field relationships should not change status."""
        record = {
            "start_time": "2026-04-12 08:15",
            "end_time": "2026-04-12 08:37",
            "duration_minutes": "22",
            "distance_km": "3.4",
            "bike_id": "BIKE-0420",
            "status": "needs_cleaning"
        }
        result = cleaner.check_cross_fields(record)
        self.assertEqual(result["status"], "needs_cleaning")


class TestParseDatetime(unittest.TestCase):

    def test_standard_format_parses(self):
        """Standard YYYY-MM-DD HH:MM format should parse."""
        result = cleaner._parse_datetime("2026-04-12 08:15")
        self.assertIsNotNone(result)

    def test_slash_format_parses(self):
        """YYYY/MM/DD HH:MM format should parse."""
        result = cleaner._parse_datetime("2026/04/12 08:15")
        self.assertIsNotNone(result)

    def test_day_first_format_parses(self):
        """DD-MM-YYYY HH:MM format should parse."""
        result = cleaner._parse_datetime("12-04-2026 08:15")
        self.assertIsNotNone(result)

    def test_invalid_format_returns_none(self):
        """Unparseable datetime should return None."""
        result = cleaner._parse_datetime("not-a-date")
        self.assertIsNone(result)

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        result = cleaner._parse_datetime("")
        self.assertIsNone(result)

    def test_none_returns_none(self):
        """None should return None."""
        result = cleaner._parse_datetime(None)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
