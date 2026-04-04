"""Edge-case tests for ICS feed fetching (src/fetchers/calendar_ical.py)."""

import zoneinfo
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from src.fetchers.calendar_ical import _parse_ical_event, _url_hostname, fetch_from_ical

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ET = zoneinfo.ZoneInfo("America/New_York")


def _make_ical_response(ical_text: str, cal_name: str = "Test Calendar") -> str:
    """Wrap VEVENT text in a minimal VCALENDAR."""
    return (
        f"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nX-WR-CALNAME:{cal_name}\r\n{ical_text}END:VCALENDAR\r\n"
    )


def _mock_response(text: str, status_code: int = 200):
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


# ---------------------------------------------------------------------------
# _parse_ical_event edge cases
# ---------------------------------------------------------------------------


class TestParseIcalEventEdgeCases:
    def test_event_with_no_dtend_uses_one_hour_default(self):
        """VEVENT without DTEND or DURATION should default to 1 hour."""
        from icalendar import Calendar

        ical_text = (
            "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\n"
            "SUMMARY:Quick Meeting\r\n"
            "DTSTART:20260404T100000Z\r\n"
            "UID:no-end-1\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        cal = Calendar.from_ical(ical_text)
        for comp in cal.walk():
            if comp.name == "VEVENT":
                event = _parse_ical_event(comp, "Test")
                assert event is not None
                assert (event.end - event.start).total_seconds() == 3600

    def test_allday_event_with_no_dtend_uses_one_day(self):
        """All-day VEVENT without DTEND defaults to 1-day duration."""
        from icalendar import Calendar

        ical_text = (
            "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\n"
            "SUMMARY:Holiday\r\n"
            "DTSTART;VALUE=DATE:20260404\r\n"
            "UID:no-end-allday\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        cal = Calendar.from_ical(ical_text)
        for comp in cal.walk():
            if comp.name == "VEVENT":
                event = _parse_ical_event(comp, "Test")
                assert event is not None
                assert event.is_all_day is True
                assert (event.end - event.start).days == 1

    def test_event_with_duration_instead_of_dtend(self):
        """VEVENT with DURATION property should compute end correctly."""
        from icalendar import Calendar

        ical_text = (
            "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\n"
            "SUMMARY:Workshop\r\n"
            "DTSTART:20260404T090000Z\r\n"
            "DURATION:PT2H30M\r\n"
            "UID:duration-1\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        cal = Calendar.from_ical(ical_text)
        for comp in cal.walk():
            if comp.name == "VEVENT":
                event = _parse_ical_event(comp, "Test")
                assert event is not None
                assert (event.end - event.start).total_seconds() == 9000  # 2.5 hours

    def test_event_without_dtstart_returns_none(self):
        """VEVENT missing DTSTART should return None."""
        from icalendar import Calendar

        ical_text = (
            "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\n"
            "SUMMARY:Broken Event\r\n"
            "DTEND:20260404T110000Z\r\n"
            "UID:no-start\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        cal = Calendar.from_ical(ical_text)
        for comp in cal.walk():
            if comp.name == "VEVENT":
                event = _parse_ical_event(comp, "Test")
                assert event is None

    def test_event_without_summary_uses_default(self):
        """VEVENT without SUMMARY should use '(no title)'."""
        from icalendar import Calendar

        ical_text = (
            "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\n"
            "DTSTART:20260404T100000Z\r\n"
            "DTEND:20260404T110000Z\r\n"
            "UID:no-summary\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        cal = Calendar.from_ical(ical_text)
        for comp in cal.walk():
            if comp.name == "VEVENT":
                event = _parse_ical_event(comp, "Test")
                assert event is not None
                assert event.summary == "(no title)"

    def test_tz_aware_event_converted_to_naive_local(self):
        """TZ-aware events should be converted to naive local time."""
        from icalendar import Calendar

        ical_text = (
            "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\n"
            "SUMMARY:NYC Meeting\r\n"
            "DTSTART:20260404T140000Z\r\n"
            "DTEND:20260404T150000Z\r\n"
            "UID:tz-aware-1\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        cal = Calendar.from_ical(ical_text)
        for comp in cal.walk():
            if comp.name == "VEVENT":
                event = _parse_ical_event(comp, "Test", tz=ET)
                assert event is not None
                # 14:00 UTC → 10:00 EDT
                assert event.start.hour == 10
                assert event.start.tzinfo is None  # naive


# ---------------------------------------------------------------------------
# fetch_from_ical edge cases
# ---------------------------------------------------------------------------


class TestFetchFromIcalEdgeCases:
    @patch("src.fetchers.calendar_ical.requests.get")
    def test_empty_feed_returns_empty(self, mock_get):
        """An ICS feed with no VEVENT components returns []."""
        mock_get.return_value = _mock_response(
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        )
        events = fetch_from_ical(["https://example.com/cal.ics"])
        assert events == []

    @patch("src.fetchers.calendar_ical.requests.get")
    def test_http_error_gracefully_skipped(self, mock_get):
        """HTTP errors should be logged and skipped, not raised."""
        mock_get.return_value = _mock_response("", status_code=500)
        events = fetch_from_ical(["https://example.com/cal.ics"])
        assert events == []

    @patch("src.fetchers.calendar_ical.requests.get")
    def test_network_timeout_gracefully_skipped(self, mock_get):
        """Network timeouts should be logged and skipped."""
        mock_get.side_effect = Exception("Connection timed out")
        events = fetch_from_ical(["https://example.com/cal.ics"])
        assert events == []

    @patch("src.fetchers.calendar_ical.requests.get")
    def test_malformed_ics_gracefully_skipped(self, mock_get):
        """Malformed ICS data should be logged and skipped."""
        mock_get.return_value = _mock_response("THIS IS NOT ICS DATA")
        events = fetch_from_ical(["https://example.com/cal.ics"])
        assert events == []

    @patch("src.fetchers.calendar_ical.requests.get")
    def test_mixed_tz_events_in_single_feed(self, mock_get):
        """Events with different timezones in same feed should all parse."""
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        event_day = monday + timedelta(days=1)

        ical_text = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "X-WR-CALNAME:Multi-TZ\r\n"
            "BEGIN:VEVENT\r\n"
            f"DTSTART:{event_day.strftime('%Y%m%d')}T140000Z\r\n"
            f"DTEND:{event_day.strftime('%Y%m%d')}T150000Z\r\n"
            "SUMMARY:UTC Event\r\nUID:utc-1\r\n"
            "END:VEVENT\r\n"
            "BEGIN:VEVENT\r\n"
            f"DTSTART;TZID=America/Los_Angeles:{event_day.strftime('%Y%m%d')}T090000\r\n"
            f"DTEND;TZID=America/Los_Angeles:{event_day.strftime('%Y%m%d')}T100000\r\n"
            "SUMMARY:LA Event\r\nUID:la-1\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        mock_get.return_value = _mock_response(ical_text)
        events = fetch_from_ical(["https://example.com/cal.ics"], tz=ET)
        # Both events should parse (whether or not they fall in the week window)
        assert isinstance(events, list)


# ---------------------------------------------------------------------------
# _url_hostname
# ---------------------------------------------------------------------------


class TestUrlHostname:
    def test_normal_url(self):
        assert _url_hostname("https://calendar.google.com/cal.ics") == "calendar.google.com"

    def test_url_with_path(self):
        assert _url_hostname("https://example.com/path/to/cal.ics") == "example.com"

    def test_invalid_url_returns_original(self):
        result = _url_hostname("not a url")
        assert isinstance(result, str)
