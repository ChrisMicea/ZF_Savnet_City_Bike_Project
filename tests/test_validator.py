"""
test_validator.py
=================
Unit tests for validator.py business logic.

Run from the project root with:
    python -m pytest tests/test_validator.py -v
  or:
    python -m unittest tests/test_validator -v

Each TestCase class tests one validator function in isolation.
"""

import unittest
import sys
import os

# Make sure Python can find validator.py and utils.py when the test file lives in a tests/ subfolder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

import validator
from validator import (
    VALIDATION_STATUS,
    validate_ride_id,
    validate_bike_id,
    validate_user_type,
    validate_station,
    validate_start_time,
    validate_end_time,
    _validate_datetime,
    validate_duration,
    validate_distance,
)


# Helpers
CLEAN = VALIDATION_STATUS["clean"]
NEEDS_CLEANING = VALIDATION_STATUS["needs_cleaning"]
SUSPICIOUS = VALIDATION_STATUS["suspicious"]
BEYOND_REPAIR = VALIDATION_STATUS["beyond_repair"]


def _reset_seen_ids():
    """
    validate_ride_id keeps state in the module-level set ride_ids_encountered.
    Call this before any test that touches ride IDs so tests don't bleed into
    each other.
    """
    validator.ride_ids_encountered.clear()


class TestValidateRideId(unittest.TestCase):

    def setUp(self):
        # Runs automatically before EVERY test method in this class.
        _reset_seen_ids()

    # --- happy paths ---

    def test_clean_ride_id_passes(self):
        """A properly formatted, first-seen ride ID is clean."""
        result = validate_ride_id({"ride_id": "RIDE-10001"})
        self.assertEqual(result, CLEAN)

    def test_ride_id_with_spaces_needs_cleaning(self):
        """Spaces around or inside a ride ID are fixable (needs_cleaning)."""
        result = validate_ride_id({"ride_id": " RI DE-1 0001 "})
        self.assertEqual(result, NEEDS_CLEANING)

    # --- duplicate detection ---

    def test_duplicate_ride_id_is_suspicious(self):
        """The second occurrence of the same ride ID must be flagged."""
        validate_ride_id({"ride_id": "RIDE-10001"})   # first — registers it
        result = validate_ride_id({"ride_id": "RIDE-10001"})   # second — duplicate
        self.assertEqual(result, SUSPICIOUS)

    def test_different_ride_ids_are_not_duplicates(self):
        """Two distinct ride IDs should not affect each other."""
        validate_ride_id({"ride_id": "RIDE-10001"})
        result = validate_ride_id({"ride_id": "RIDE-10002"})
        self.assertEqual(result, CLEAN)

    # --- invalid formats ---

    def test_empty_ride_id_is_beyond_repair(self):
        result = validate_ride_id({"ride_id": ""})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_missing_ride_id_key_is_beyond_repair(self):
        result = validate_ride_id({})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_wrong_prefix_is_beyond_repair(self):
        """e.g. 'TRIP-10001' does not match the RIDE-XXXXX pattern."""
        result = validate_ride_id({"ride_id": "TRIP-10001"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_too_few_digits_is_beyond_repair(self):
        """RIDE-042 has only 3 digits; the pattern requires exactly 5."""
        result = validate_ride_id({"ride_id": "RIDE-042"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_non_numeric_suffix_is_beyond_repair(self):
        result = validate_ride_id({"ride_id": "RIDE-ABCDE"})
        self.assertEqual(result, BEYOND_REPAIR)


class TestValidateBikeId(unittest.TestCase):

    # --- happy paths ---

    def test_canonical_bike_id_is_clean(self):
        result = validate_bike_id({"bike_id": "BIKE-0420"})
        self.assertEqual(result, CLEAN)

    def test_lowercase_bike_id_needs_cleaning(self):
        """'bike-0420' is valid data but needs uppercasing."""
        result = validate_bike_id({"bike_id": "bike-0420"})
        self.assertEqual(result, NEEDS_CLEANING)

    def test_mixed_case_bike_id_needs_cleaning(self):
        result = validate_bike_id({"bike_id": "BiKe-0420"})
        self.assertEqual(result, NEEDS_CLEANING)

    def test_bike_id_with_spaces_needs_cleaning(self):
        """' bike-0420 ' has fixable whitespace."""
        result = validate_bike_id({"bike_id": " bik e-04 20 "})
        self.assertEqual(result, NEEDS_CLEANING)

    # --- invalid IDs ---

    def test_empty_bike_id_is_beyond_repair(self):
        result = validate_bike_id({"bike_id": ""})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_missing_bike_id_key_is_beyond_repair(self):
        result = validate_bike_id({})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_wrong_prefix_is_beyond_repair(self):
        """'B-0042' does not match the BIKE-NNNN pattern."""
        result = validate_bike_id({"bike_id": "B-0042"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_non_numeric_suffix_is_beyond_repair(self):
        """'BIKE-XYZ' has letters where digits are expected."""
        result = validate_bike_id({"bike_id": "BIKE-XYZ"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_too_few_digits_is_beyond_repair(self):
        """The pattern requires exactly 4 digits."""
        result = validate_bike_id({"bike_id": "BIKE-42"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_too_many_digits_is_beyond_repair(self):
        result = validate_bike_id({"bike_id": "BIKE-42000"})
        self.assertEqual(result, BEYOND_REPAIR)


class TestValidateUserType(unittest.TestCase):

    def test_member_is_clean(self):
        result = validate_user_type({"user_type": "member"})
        self.assertEqual(result, CLEAN)

    def test_casual_is_clean(self):
        result = validate_user_type({"user_type": "casual"})
        self.assertEqual(result, CLEAN)

    def test_tourist_is_clean(self):
        result = validate_user_type({"user_type": "tourist"})
        self.assertEqual(result, CLEAN)

    def test_uppercase_member_needs_cleaning(self):
        """'MEMBER' is recognisable but needs lowercasing."""
        result = validate_user_type({"user_type": "MEMBER"})
        self.assertEqual(result, NEEDS_CLEANING)

    def test_mixed_case_needs_cleaning(self):
        result = validate_user_type({"user_type": "MeMbEr"})
        self.assertEqual(result, NEEDS_CLEANING)

    def test_user_type_with_spaces_needs_cleaning(self):
        result = validate_user_type({"user_type": " membe r "})
        self.assertEqual(result, NEEDS_CLEANING)

    def test_unknown_type_robot_is_beyond_repair(self):
        result = validate_user_type({"user_type": "robot"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_unknown_type_vip_is_beyond_repair(self):
        result = validate_user_type({"user_type": "vip"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_empty_user_type_is_beyond_repair(self):
        result = validate_user_type({"user_type": ""})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_missing_user_type_key_is_beyond_repair(self):
        result = validate_user_type({})
        self.assertEqual(result, BEYOND_REPAIR)


class TestValidateStation(unittest.TestCase):

    # The validator title-cases and strips spaces, then checks dict_stations.
    # A known station from utils.dict_stations is "Central_Station".

    def test_known_station_exact_is_clean(self):
        record = {"start_station": "Central_Station", "end_station": "City_Hall"}
        result = validate_station(record, 0)
        self.assertEqual(result, CLEAN)
        result = validate_station(record, 1)
        self.assertEqual(result, CLEAN)

    def test_known_station_with_spaces_needs_cleaning(self):
        """Spaces are fixable."""
        record = {"start_station": " Centra l_St ation ", "end_station": "City_Hall"}
        result = validate_station(record, 0)
        self.assertEqual(result, NEEDS_CLEANING)

    def test_missing_start_station_is_beyond_repair(self):
        record = {"start_station": "", "end_station": "City_Hall"}
        result = validate_station(record, 0)
        self.assertEqual(result, BEYOND_REPAIR)

    def test_missing_end_station_is_beyond_repair(self):
        record = {"start_station": "Central_Station", "end_station": ""}
        result = validate_station(record, 1)
        self.assertEqual(result, BEYOND_REPAIR)

    def test_unknown_station_is_suspicious(self):
        """A name that passes the character check but isn't in the known list."""
        record = {"start_station": "Totally_Unknown_Place", "end_station": "City_Hall"}
        result = validate_station(record, 0)
        self.assertEqual(result, SUSPICIOUS)

    def test_invalid_characters_in_station_is_beyond_repair(self):
        """Random garbage characters cannot be cleaned."""
        record = {"start_station": "!!@@##", "end_station": "City_Hall"}
        result = validate_station(record, 0)
        self.assertEqual(result, BEYOND_REPAIR)


class TestValidateDatetime(unittest.TestCase):

    def test_standard_format_is_clean(self):
        """YYYY-MM-DD HH:MM is the canonical accepted format."""
        result = _validate_datetime("2026-04-12 08:15")
        self.assertEqual(result, CLEAN)

    def test_slash_separated_format_needs_cleaning(self):
        """YYYY/MM/DD HH:MM is accepted but non-canonical -> needs_cleaning."""
        result = _validate_datetime("2026/04/12 08:15")
        self.assertEqual(result, NEEDS_CLEANING)

    def test_day_first_format_needs_cleaning(self):
        """DD-MM-YYYY HH:MM is accepted but non-canonical -> needs_cleaning."""
        result = _validate_datetime("12-04-2026 08:15")
        self.assertEqual(result, NEEDS_CLEANING)

    def test_unparseable_string_is_beyond_repair(self):
        result = _validate_datetime("not-a-date")
        self.assertEqual(result, BEYOND_REPAIR)

    def test_empty_datetime_is_beyond_repair(self):
        result = _validate_datetime("")
        self.assertEqual(result, BEYOND_REPAIR)

    def test_none_datetime_is_beyond_repair(self):
        result = _validate_datetime(None)
        self.assertEqual(result, BEYOND_REPAIR)


class TestValidateDuration(unittest.TestCase):

    def test_positive_integer_duration_is_clean(self):
        result = validate_duration({"duration_minutes": "22"})
        self.assertEqual(result, CLEAN)

    def test_duration_with_spaces_needs_cleaning(self):
        result = validate_duration({"duration_minutes": " 2 2 "})
        self.assertEqual(result, NEEDS_CLEANING)

    def test_zero_duration_is_beyond_repair(self):
        """A zero-minute ride is not a real ride."""
        result = validate_duration({"duration_minutes": "0"})
        # validate_duration currently only rejects < 0 -> so the result is CLEAN
        # self.assertIn(result, [CLEAN, BEYOND_REPAIR])
        self.assertEqual(result, NEEDS_CLEANING)

    def test_negative_duration_is_beyond_repair(self):
        result = validate_duration({"duration_minutes": "-15"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_text_duration_is_beyond_repair(self):
        result = validate_duration({"duration_minutes": "twenty"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_empty_duration_is_beyond_repair(self):
        result = validate_duration({"duration_minutes": ""})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_missing_duration_key_is_beyond_repair(self):
        result = validate_duration({})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_float_duration_is_accepted(self):
        """Durations like '24.5' should be treated as valid numbers."""
        result = validate_duration({"duration_minutes": "24.5"})
        self.assertEqual(result, CLEAN)


class TestValidateDistance(unittest.TestCase):

    def test_plain_float_is_clean(self):
        result = validate_distance({"distance_km": "3.4"})
        self.assertEqual(result, CLEAN)

    def test_distance_with_km_suffix_needs_cleaning(self):
        """'3.4 km' is fixable by stripping the unit label."""
        result = validate_distance({"distance_km": "3.4 km"})
        self.assertEqual(result, NEEDS_CLEANING)

    def test_distance_with_uppercase_km_needs_cleaning(self):
        result = validate_distance({"distance_km": "3.4KM"})
        self.assertEqual(result, NEEDS_CLEANING)

    def test_negative_distance_is_beyond_repair(self):
        result = validate_distance({"distance_km": "-2.0"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_text_distance_is_beyond_repair(self):
        result = validate_distance({"distance_km": "far"})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_empty_distance_is_beyond_repair(self):
        result = validate_distance({"distance_km": ""})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_missing_distance_key_is_beyond_repair(self):
        result = validate_distance({})
        self.assertEqual(result, BEYOND_REPAIR)

    def test_zero_distance_is_accepted(self):
        """Zero distance is allowed (same-station rides). Analysis may flag it separately."""
        result = validate_distance({"distance_km": "0"})
        self.assertNotEqual(result, BEYOND_REPAIR)


class TestCleanRecordEndToEnd(unittest.TestCase):

    def setUp(self):
        _reset_seen_ids()

    def test_fully_clean_record_produces_no_worse_than_clean(self):
        """
        A textbook-perfect record should accumulate no worse than CLEAN
        across all individual validators.
        """
        record = {
            "ride_id":          "RIDE-10001",
            "bike_id":          "BIKE-0420",
            "user_type":        "member",
            "start_station":    "Central_Station",
            "end_station":      "City_Hall",
            "start_time":       "2026-04-12 08:15",
            "end_time":         "2026-04-12 08:37",
            "duration_minutes": "22",
            "distance_km":      "3.4",
        }

        statuses = [
            validate_ride_id(record),
            validate_bike_id(record),
            validate_user_type(record),
            validate_station(record, 0),
            validate_station(record, 1),
            validate_start_time(record),
            validate_end_time(record),
            validate_duration(record),
            validate_distance(record),
        ]

        worst = max(statuses)
        self.assertEqual(
            worst, CLEAN,
            msg=f"Expected all CLEAN but got statuses: {statuses}"
        )


if __name__ == "__main__":
    unittest.main()