"""
test_anomaly_detector.py
========================
Unit tests for anomaly_detector.py business logic.

Run from the project root with:
    python -m pytest tests/test_anomaly_detector.py -v
  or:
    python -m unittest tests.test_anomaly_detector -v

Each TestCase class tests one anomaly detector function in isolation.
"""

import unittest
import sys
import os

# Make sure Python can find anomaly_detector.py and utils.py when the test file lives in a tests/ subfolder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

import anomaly_detector
import utils


class TestDetectBikeOverlap(unittest.TestCase):

    def test_detects_overlapping_rides(self):
        """Should detect when a bike has overlapping rides."""
        records = [
            {
                "bike_id": "BIKE-0420",
                "ride_id": "RIDE-1",
                "start_time": "2026-04-06 08:00",
                "end_time": "2026-04-06 09:00",
            },
            {
                "bike_id": "BIKE-0420",
                "ride_id": "RIDE-2",
                "start_time": "2026-04-06 08:30",
                "end_time": "2026-04-06 09:30",
            },
        ]
        result = anomaly_detector.detect_bike_overlap(records)
        self.assertEqual(result["total_bikes_with_overlap"], 1)
        self.assertEqual(len(result["overlapping_bikes"]), 1)
        self.assertEqual(result["overlapping_bikes"][0]["bike_id"], "BIKE-0420")

    def test_no_overlap_with_sequential_rides(self):
        """Should not flag sequential rides that don't overlap."""
        records = [
            {
                "bike_id": "BIKE-0420",
                "ride_id": "RIDE-1",
                "start_time": "2026-04-06 08:00",
                "end_time": "2026-04-06 09:00",
            },
            {
                "bike_id": "BIKE-0420",
                "ride_id": "RIDE-2",
                "start_time": "2026-04-06 09:00",
                "end_time": "2026-04-06 10:00",
            },
        ]
        result = anomaly_detector.detect_bike_overlap(records)
        self.assertEqual(result["total_bikes_with_overlap"], 0)
        self.assertEqual(len(result["overlapping_bikes"]), 0)

    def test_multiple_bikes_with_overlaps(self):
        """Should detect overlaps across multiple bikes."""
        records = [
            {
                "bike_id": "BIKE-0420",
                "ride_id": "RIDE-1",
                "start_time": "2026-04-06 08:00",
                "end_time": "2026-04-06 09:00",
            },
            {
                "bike_id": "BIKE-0420",
                "ride_id": "RIDE-2",
                "start_time": "2026-04-06 08:30",
                "end_time": "2026-04-06 09:30",
            },
            {
                "bike_id": "BIKE-0421",
                "ride_id": "RIDE-3",
                "start_time": "2026-04-06 10:00",
                "end_time": "2026-04-06 11:00",
            },
            {
                "bike_id": "BIKE-0421",
                "ride_id": "RIDE-4",
                "start_time": "2026-04-06 10:30",
                "end_time": "2026-04-06 11:30",
            },
        ]
        result = anomaly_detector.detect_bike_overlap(records)
        self.assertEqual(result["total_bikes_with_overlap"], 2)

    def test_handles_empty_list(self):
        """Empty list should return no overlaps."""
        result = anomaly_detector.detect_bike_overlap([])
        self.assertEqual(result["total_bikes_with_overlap"], 0)
        self.assertEqual(result["total_rides_checked"], 0)

    def test_calculates_overlap_minutes(self):
        """Should calculate the overlap duration in minutes."""
        records = [
            {
                "bike_id": "BIKE-0420",
                "ride_id": "RIDE-1",
                "start_time": "2026-04-06 08:00",
                "end_time": "2026-04-06 09:00",
            },
            {
                "bike_id": "BIKE-0420",
                "ride_id": "RIDE-2",
                "start_time": "2026-04-06 08:30",
                "end_time": "2026-04-06 09:30",
            },
        ]
        result = anomaly_detector.detect_bike_overlap(records)
        # Overlap is 30 minutes (08:30 to 09:00)
        self.assertEqual(result["overlapping_bikes"][0]["overlap_minutes"], 30.0)


class TestDetectStationSpike(unittest.TestCase):

    def test_detects_spike_in_start_station(self):
        """Should detect start stations with usage above 3x average."""
        records = [
            {"start_station": "Central_Station"},
            {"start_station": "Central_Station"},
            {"start_station": "Central_Station"},
            {"start_station": "City_Hall"},
        ]
        result = anomaly_detector.detect_station_spike(records)
        # Average = 1, Central_Station has 3 (3x average)
        self.assertEqual(len(result["spiked_start_stations"]), 1)
        self.assertEqual(result["spiked_start_stations"][0]["station"], "Central_Station")

    def test_detects_spike_in_end_station(self):
        """Should detect end stations with usage above 3x average."""
        records = [
            {"end_station": "City_Hall"},
            {"end_station": "City_Hall"},
            {"end_station": "City_Hall"},
            {"end_station": "Central_Station"},
        ]
        result = anomaly_detector.detect_station_spike(records)
        self.assertEqual(len(result["spiked_end_stations"]), 1)
        self.assertEqual(result["spiked_end_stations"][0]["station"], "City_Hall")

    def test_no_spike_when_usage_is_normal(self):
        """Should not flag stations with normal usage."""
        records = [
            {"start_station": "Central_Station"},
            {"start_station": "City_Hall"},
            {"end_station": "Central_Station"},
            {"end_station": "City_Hall"},
        ]
        result = anomaly_detector.detect_station_spike(records)
        self.assertEqual(len(result["spiked_start_stations"]), 0)
        self.assertEqual(len(result["spiked_end_stations"]), 0)

    def test_handles_empty_list(self):
        """Empty list should return zero averages and no spikes."""
        result = anomaly_detector.detect_station_spike([])
        self.assertEqual(result["average_start_usage"], 0)
        self.assertEqual(result["average_end_usage"], 0)
        self.assertEqual(len(result["spiked_start_stations"]), 0)

    def test_calculates_ratio(self):
        """Should calculate the ratio of station usage to average."""
        records = [
            {"start_station": "Central_Station"},
            {"start_station": "Central_Station"},
            {"start_station": "Central_Station"},
            {"start_station": "City_Hall"},
        ]
        result = anomaly_detector.detect_station_spike(records)
        # Average = 1, Central_Station has 3, ratio = 3.0
        self.assertEqual(result["spiked_start_stations"][0]["ratio"], 3.0)


class TestDetectRouteSpike(unittest.TestCase):

    def test_detects_spike_in_route(self):
        """Should detect routes with usage above 3x average."""
        records = [
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "City_Hall", "end_station": "Central_Station"},
        ]
        result = anomaly_detector.detect_route_spike(records)
        self.assertEqual(len(result["spiked_routes"]), 1)
        self.assertEqual(result["spiked_routes"][0]["route"], "Central_Station -> City_Hall")

    def test_no_spike_when_route_usage_is_normal(self):
        """Should not flag routes with normal usage."""
        records = [
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "City_Hall", "end_station": "Central_Station"},
        ]
        result = anomaly_detector.detect_route_spike(records)
        self.assertEqual(len(result["spiked_routes"]), 0)

    def test_handles_empty_list(self):
        """Empty list should return zero average and no spikes."""
        result = anomaly_detector.detect_route_spike([])
        self.assertEqual(result["average_route_usage"], 0)
        self.assertEqual(len(result["spiked_routes"]), 0)

    def test_sorts_by_count_descending(self):
        """Should sort spiked routes by count in descending order."""
        records = [
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "City_Hall", "end_station": "Central_Station"},
            {"start_station": "City_Hall", "end_station": "Central_Station"},
        ]
        result = anomaly_detector.detect_route_spike(records)
        # Both routes have counts above threshold, should be sorted
        self.assertTrue(result["spiked_routes"][0]["count"] >= result["spiked_routes"][1]["count"])

    def test_ignores_missing_stations(self):
        """Should ignore records with missing start or end stations."""
        records = [
            {"start_station": "Central_Station", "end_station": "City_Hall"},
            {"start_station": "Central_Station"},
            {"end_station": "City_Hall"},
        ]
        result = anomaly_detector.detect_route_spike(records)
        self.assertEqual(result["total_routes"], 1)


class TestDetectZeroDuration(unittest.TestCase):

    def test_detects_zero_duration_with_different_stations(self):
        """Should flag rides with zero duration and different stations."""
        records = [
            {
                "duration_minutes": 0,
                "start_station": "Central_Station",
                "end_station": "City_Hall",
            },
        ]
        result = anomaly_detector.detect_zero_duration(records)
        self.assertEqual(result["count"], 1)
        self.assertEqual(len(result["zero_duration_rides"]), 1)

    def test_ignores_zero_duration_same_station(self):
        """Should not flag zero duration rides with same start and end station."""
        records = [
            {
                "duration_minutes": 0,
                "start_station": "Central_Station",
                "end_station": "Central_Station",
            },
        ]
        result = anomaly_detector.detect_zero_duration(records)
        self.assertEqual(result["count"], 0)

    def test_ignores_positive_duration(self):
        """Should not flag rides with positive duration."""
        records = [
            {
                "duration_minutes": 10,
                "start_station": "Central_Station",
                "end_station": "City_Hall",
            },
        ]
        result = anomaly_detector.detect_zero_duration(records)
        self.assertEqual(result["count"], 0)

    def test_handles_empty_list(self):
        """Empty list should return zero count."""
        result = anomaly_detector.detect_zero_duration([])
        self.assertEqual(result["count"], 0)


class TestDetectStrangeDistanceDuration(unittest.TestCase):

    def test_detects_high_distance_short_duration(self):
        """Should flag rides with high distance but very short duration."""
        records = [
            {
                "ride_id": "RIDE-1",
                "distance_km": "25.0",
                "duration_minutes": "3",
            },
        ]
        result = anomaly_detector.detect_strange_distance_duration(records)
        self.assertEqual(result["total_suspicious"], 1)
        self.assertEqual(result["suspicious_combinations"][0]["type"], "high_distance_short_duration")

    def test_detects_low_distance_long_duration(self):
        """Should flag rides with very low distance but very long duration."""
        records = [
            {
                "ride_id": "RIDE-1",
                "distance_km": "0.1",
                "duration_minutes": "130",
            },
        ]
        result = anomaly_detector.detect_strange_distance_duration(records)
        self.assertEqual(result["total_suspicious"], 1)
        self.assertEqual(result["suspicious_combinations"][0]["type"], "low_distance_long_duration")

    def test_ignores_normal_combinations(self):
        """Should not flag normal distance/duration combinations."""
        records = [
            {
                "ride_id": "RIDE-1",
                "distance_km": "5.0",
                "duration_minutes": "15",
            },
        ]
        result = anomaly_detector.detect_strange_distance_duration(records)
        self.assertEqual(result["total_suspicious"], 0)

    def test_calculates_speed(self):
        """Should calculate speed for suspicious combinations."""
        records = [
            {
                "ride_id": "RIDE-1",
                "distance_km": "30.0",
                "duration_minutes": "4",
            },
        ]
        result = anomaly_detector.detect_strange_distance_duration(records)
        # Speed = (30 / 4) * 60 = 450 kph
        self.assertEqual(result["suspicious_combinations"][0]["speed_kph"], 450.0)

    def test_handles_invalid_values(self):
        """Should handle invalid distance or duration values gracefully."""
        records = [
            {
                "ride_id": "RIDE-1",
                "distance_km": "invalid",
                "duration_minutes": "10",
            },
        ]
        result = anomaly_detector.detect_strange_distance_duration(records)
        self.assertEqual(result["total_suspicious"], 0)


class TestDetectBikesWithMostSuspiciousRecords(unittest.TestCase):

    def test_counts_suspicious_records_by_bike(self):
        """Should count suspicious records by bike ID."""
        records = [
            {"status": "suspicious", "bike_id": "BIKE-0420"},
            {"status": "suspicious", "bike_id": "BIKE-0420"},
            {"status": "suspicious", "bike_id": "BIKE-0421"},
            {"status": "clean", "bike_id": "BIKE-0420"},
        ]
        result = anomaly_detector.detect_bikes_with_most_suspicious_records(records)
        self.assertEqual(result["total_bikes_with_suspicious"], 2)
        self.assertEqual(len(result["top_suspicious_bikes"]), 2)

    def test_includes_beyond_repair_status(self):
        """Should include beyond_repair status in suspicious counts."""
        records = [
            {"status": "beyond_repair", "bike_id": "BIKE-0420"},
            {"status": "suspicious", "bike_id": "BIKE-0420"},
        ]
        result = anomaly_detector.detect_bikes_with_most_suspicious_records(records)
        self.assertEqual(result["top_suspicious_bikes"][0]["suspicious_count"], 2)

    def test_ignores_clean_and_fixed_status(self):
        """Should ignore clean and fixed status."""
        records = [
            {"status": "clean", "bike_id": "BIKE-0420"},
            {"status": "fixed", "bike_id": "BIKE-0420"},
        ]
        result = anomaly_detector.detect_bikes_with_most_suspicious_records(records)
        self.assertEqual(result["total_bikes_with_suspicious"], 0)

    def test_returns_top_10_bikes(self):
        """Should return top 10 bikes by suspicious count."""
        records = []
        for i in range(15):
            records.append({"status": "suspicious", "bike_id": f"BIKE-{i:04d}"})
        result = anomaly_detector.detect_bikes_with_most_suspicious_records(records)
        self.assertEqual(len(result["top_suspicious_bikes"]), 10)

    def test_handles_empty_list(self):
        """Empty list should return zero counts."""
        result = anomaly_detector.detect_bikes_with_most_suspicious_records([])
        self.assertEqual(result["total_bikes_with_suspicious"], 0)
        self.assertEqual(len(result["top_suspicious_bikes"]), 0)


class TestDetectStationsWithMostSuspiciousRecords(unittest.TestCase):

    def test_counts_suspicious_records_by_start_station(self):
        """Should count suspicious records by start station."""
        records = [
            {"status": "suspicious", "start_station": "Central_Station"},
            {"status": "suspicious", "start_station": "Central_Station"},
            {"status": "suspicious", "start_station": "City_Hall"},
        ]
        result = anomaly_detector.detect_stations_with_most_suspicious_records(records)
        self.assertEqual(len(result["top_suspicious_start_stations"]), 2)
        self.assertEqual(result["top_suspicious_start_stations"][0]["station"], "Central_Station")
        self.assertEqual(result["top_suspicious_start_stations"][0]["suspicious_count"], 2)

    def test_counts_suspicious_records_by_end_station(self):
        """Should count suspicious records by end station."""
        records = [
            {"status": "suspicious", "end_station": "City_Hall"},
            {"status": "suspicious", "end_station": "City_Hall"},
            {"status": "suspicious", "end_station": "Central_Station"},
        ]
        result = anomaly_detector.detect_stations_with_most_suspicious_records(records)
        self.assertEqual(len(result["top_suspicious_end_stations"]), 2)
        self.assertEqual(result["top_suspicious_end_stations"][0]["station"], "City_Hall")

    def test_includes_beyond_repair_status(self):
        """Should include beyond_repair status in suspicious counts."""
        records = [
            {"status": "beyond_repair", "start_station": "Central_Station"},
            {"status": "suspicious", "start_station": "Central_Station"},
        ]
        result = anomaly_detector.detect_stations_with_most_suspicious_records(records)
        self.assertEqual(result["top_suspicious_start_stations"][0]["suspicious_count"], 2)

    def test_ignores_clean_and_fixed_status(self):
        """Should ignore clean and fixed status."""
        records = [
            {"status": "clean", "start_station": "Central_Station"},
            {"status": "fixed", "start_station": "Central_Station"},
        ]
        result = anomaly_detector.detect_stations_with_most_suspicious_records(records)
        self.assertEqual(len(result["top_suspicious_start_stations"]), 0)

    def test_returns_top_10_stations(self):
        """Should return top 10 stations by suspicious count."""
        records = []
        for i in range(15):
            records.append({"status": "suspicious", "start_station": f"Station_{i}"})
        result = anomaly_detector.detect_stations_with_most_suspicious_records(records)
        self.assertEqual(len(result["top_suspicious_start_stations"]), 10)

    def test_handles_empty_list(self):
        """Empty list should return empty lists."""
        result = anomaly_detector.detect_stations_with_most_suspicious_records([])
        self.assertEqual(len(result["top_suspicious_start_stations"]), 0)
        self.assertEqual(len(result["top_suspicious_end_stations"]), 0)


class TestDetectDuplicateRideIds(unittest.TestCase):

    def test_detects_duplicate_ride_ids(self):
        """Should detect ride IDs that appear more than once."""
        records = [
            {"ride_id": "RIDE-1"},
            {"ride_id": "RIDE-1"},
            {"ride_id": "RIDE-2"},
        ]
        result = anomaly_detector.detect_duplicate_ride_ids(records)
        self.assertEqual(result["total_duplicates"], 1)
        self.assertEqual(result["duplicate_ride_ids"][0]["ride_id"], "RIDE-1")
        self.assertEqual(result["duplicate_ride_ids"][0]["count"], 2)

    def test_no_duplicates_with_unique_ids(self):
        """Should not flag unique ride IDs."""
        records = [
            {"ride_id": "RIDE-1"},
            {"ride_id": "RIDE-2"},
            {"ride_id": "RIDE-3"},
        ]
        result = anomaly_detector.detect_duplicate_ride_ids(records)
        self.assertEqual(result["total_duplicates"], 0)

    def test_handles_multiple_duplicates(self):
        """Should detect multiple duplicate ride IDs."""
        records = [
            {"ride_id": "RIDE-1"},
            {"ride_id": "RIDE-1"},
            {"ride_id": "RIDE-2"},
            {"ride_id": "RIDE-2"},
            {"ride_id": "RIDE-2"},
        ]
        result = anomaly_detector.detect_duplicate_ride_ids(records)
        self.assertEqual(result["total_duplicates"], 2)

    def test_ignores_empty_ride_ids(self):
        """Should ignore empty ride IDs."""
        records = [
            {"ride_id": ""},
            {"ride_id": ""},
            {"ride_id": "RIDE-1"},
        ]
        result = anomaly_detector.detect_duplicate_ride_ids(records)
        self.assertEqual(result["total_duplicates"], 0)

    def test_handles_empty_list(self):
        """Empty list should return zero duplicates."""
        result = anomaly_detector.detect_duplicate_ride_ids([])
        self.assertEqual(result["total_duplicates"], 0)


class TestDetectUnknownStations(unittest.TestCase):

    def test_detects_empty_start_station(self):
        """Should flag records with empty start station."""
        records = [
            {"start_station": "", "end_station": "City_Hall"},
        ]
        result = anomaly_detector.detect_unknown_stations(records)
        self.assertEqual(result["total_unknown_stations"], 1)

    def test_detects_empty_end_station(self):
        """Should flag records with empty end station."""
        records = [
            {"start_station": "Central_Station", "end_station": ""},
        ]
        result = anomaly_detector.detect_unknown_stations(records)
        self.assertEqual(result["total_unknown_stations"], 1)

    def test_detects_whitespace_only_stations(self):
        """Should flag records with whitespace-only stations."""
        records = [
            {"start_station": "   ", "end_station": "City_Hall"},
        ]
        result = anomaly_detector.detect_unknown_stations(records)
        self.assertEqual(result["total_unknown_stations"], 1)

    def test_ignores_valid_stations(self):
        """Should not flag records with valid stations."""
        records = [
            {"start_station": "Central_Station", "end_station": "City_Hall"},
        ]
        result = anomaly_detector.detect_unknown_stations(records)
        self.assertEqual(result["total_unknown_stations"], 0)

    def test_handles_empty_list(self):
        """Empty list should return zero count."""
        result = anomaly_detector.detect_unknown_stations([])
        self.assertEqual(result["total_unknown_stations"], 0)


if __name__ == "__main__":
    unittest.main()
