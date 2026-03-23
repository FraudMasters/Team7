"""
Tests for calendar availability API endpoints.

Tests the availability slots generation logic with business hours and conflict detection.
"""
import pytest
from datetime import datetime, time, timedelta

from backend.api.calendar import filter_slots_by_business_hours, BUSINESS_HOURS_START, BUSINESS_HOURS_END, BUSINESS_DAYS
from backend.services.calendar_service import AvailabilitySlot


class TestBusinessHoursFiltering:
    """Test suite for business hours filtering logic."""

    def test_filters_slots_before_business_hours(self):
        """Test that slots before business hours are filtered out."""
        # Create a slot at 7am (before 9am business hours start)
        start_date = datetime(2026, 3, 25, 7, 0)  # Tuesday 7am
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(hours=2),  # 7am-9am
                available=True,
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should filter out the early morning slot
        assert len(filtered) == 0

    def test_filters_slots_after_business_hours(self):
        """Test that slots after business hours are filtered out."""
        # Create a slot at 6pm (after 5pm business hours end)
        start_date = datetime(2026, 3, 25, 18, 0)  # Tuesday 6pm
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(hours=1),  # 6pm-7pm
                available=True,
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should filter out the evening slot
        assert len(filtered) == 0

    def test_includes_slots_during_business_hours(self):
        """Test that slots during business hours are included."""
        # Create a slot at 10am (within 9am-5pm business hours)
        start_date = datetime(2026, 3, 25, 10, 0)  # Tuesday 10am
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(hours=1),  # 10am-11am
                available=True,
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should include the slot during business hours
        assert len(filtered) == 1
        assert filtered[0].start_time == start_date
        assert filtered[0].end_time == start_date + timedelta(hours=1)

    def test_filters_weekend_slots(self):
        """Test that weekend slots are filtered out."""
        # Saturday and Sunday
        saturday = datetime(2026, 3, 28, 10, 0)  # Saturday 10am
        sunday = datetime(2026, 3, 29, 10, 0)    # Sunday 10am

        slots = [
            AvailabilitySlot(
                start_time=saturday,
                end_time=saturday + timedelta(hours=1),
                available=True,
                confidence=1.0
            ),
            AvailabilitySlot(
                start_time=sunday,
                end_time=sunday + timedelta(hours=1),
                available=True,
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should filter out both weekend slots
        assert len(filtered) == 0

    def test_includes_weekday_slots(self):
        """Test that weekday slots are included."""
        # Monday through Friday
        monday = datetime(2026, 3, 30, 10, 0)     # Monday 10am
        tuesday = datetime(2026, 3, 31, 10, 0)    # Tuesday 10am
        wednesday = datetime(2026, 4, 1, 10, 0)   # Wednesday 10am
        thursday = datetime(2026, 4, 2, 10, 0)    # Thursday 10am
        friday = datetime(2026, 4, 3, 10, 0)      # Friday 10am

        slots = [
            AvailabilitySlot(start_time=monday, end_time=monday + timedelta(hours=1), available=True, confidence=1.0),
            AvailabilitySlot(start_time=tuesday, end_time=tuesday + timedelta(hours=1), available=True, confidence=1.0),
            AvailabilitySlot(start_time=wednesday, end_time=wednesday + timedelta(hours=1), available=True, confidence=1.0),
            AvailabilitySlot(start_time=thursday, end_time=thursday + timedelta(hours=1), available=True, confidence=1.0),
            AvailabilitySlot(start_time=friday, end_time=friday + timedelta(hours=1), available=True, confidence=1.0),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should include all weekday slots
        assert len(filtered) == 5

    def test_splits_long_slots_into_chunks(self):
        """Test that long free slots are split into bookable chunks."""
        # Create a 3-hour slot
        start_date = datetime(2026, 3, 25, 10, 0)  # Tuesday 10am
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(hours=3),  # 10am-1pm
                available=True,
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should split into 3 one-hour slots
        assert len(filtered) == 3

        # Verify each slot is 60 minutes
        for i, slot in enumerate(filtered):
            expected_start = start_date + timedelta(hours=i)
            expected_end = expected_start + timedelta(hours=1)
            assert slot.start_time == expected_start
            assert slot.end_time == expected_end
            assert slot.available is True

    def test_clips_slot_to_business_hours(self):
        """Test that slots spanning outside business hours are clipped."""
        # Create a slot from 8am to 10am (crosses into business hours at 9am)
        start_date = datetime(2026, 3, 25, 8, 0)  # Tuesday 8am
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(hours=2),  # 8am-10am
                available=True,
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should clip to 9am-10am (1 hour slot)
        assert len(filtered) == 1
        assert filtered[0].start_time.hour == 9
        assert filtered[0].end_time.hour == 10

    def test_filters_unavailable_slots(self):
        """Test that unavailable/busy slots are filtered out."""
        start_date = datetime(2026, 3, 25, 10, 0)  # Tuesday 10am
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(hours=1),
                available=False,  # Busy slot
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should filter out unavailable slots
        assert len(filtered) == 0

    def test_filters_slots_too_short_for_duration(self):
        """Test that slots shorter than requested duration are filtered out."""
        # Create a 30-minute slot when requesting 60-minute duration
        start_date = datetime(2026, 3, 25, 10, 0)  # Tuesday 10am
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(minutes=30),  # Only 30 minutes
                available=True,
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should filter out the slot that's too short
        assert len(filtered) == 0

    def test_handles_slot_at_end_of_business_hours(self):
        """Test handling of slots at the end of business hours."""
        # Create a slot from 4pm to 6pm (business hours end at 5pm)
        start_date = datetime(2026, 3, 25, 16, 0)  # Tuesday 4pm
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(hours=2),  # 4pm-6pm
                available=True,
                confidence=1.0
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should clip to 4pm-5pm (1 hour slot)
        assert len(filtered) == 1
        assert filtered[0].start_time.hour == 16
        assert filtered[0].end_time.hour == 17

    def test_preserves_confidence_score(self):
        """Test that confidence scores are preserved in filtered slots."""
        start_date = datetime(2026, 3, 25, 10, 0)  # Tuesday 10am
        slots = [
            AvailabilitySlot(
                start_time=start_date,
                end_time=start_date + timedelta(hours=1),
                available=True,
                confidence=0.85
            ),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should preserve the confidence score
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.85

    def test_complex_scenario_multiple_slots(self):
        """Test complex scenario with multiple slots in different time periods."""
        tuesday = datetime(2026, 3, 25)
        saturday = datetime(2026, 3, 28)

        slots = [
            # Before business hours - should be filtered
            AvailabilitySlot(start_time=tuesday.replace(hour=7), end_time=tuesday.replace(hour=8), available=True, confidence=1.0),
            # During business hours - should be included (split into 2 slots)
            AvailabilitySlot(start_time=tuesday.replace(hour=10), end_time=tuesday.replace(hour=12), available=True, confidence=1.0),
            # Busy during business hours - should be filtered
            AvailabilitySlot(start_time=tuesday.replace(hour=14), end_time=tuesday.replace(hour=15), available=False, confidence=1.0),
            # After business hours - should be filtered
            AvailabilitySlot(start_time=tuesday.replace(hour=18), end_time=tuesday.replace(hour=19), available=True, confidence=1.0),
            # Weekend during business hours - should be filtered
            AvailabilitySlot(start_time=saturday.replace(hour=10), end_time=saturday.replace(hour=11), available=True, confidence=1.0),
        ]

        filtered = filter_slots_by_business_hours(slots, duration_minutes=60)

        # Should only include the 10am-12pm slot, split into 2 one-hour slots
        assert len(filtered) == 2
        assert filtered[0].start_time.hour == 10
        assert filtered[0].end_time.hour == 11
        assert filtered[1].start_time.hour == 11
        assert filtered[1].end_time.hour == 12
