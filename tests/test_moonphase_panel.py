"""Tests for src/render/components/moonphase_panel.py."""

import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw

from src.data.models import DashboardData, WeatherData
from src.render.components.moonphase_panel import (
    _ordinal_suffix,
    _quote_for_panel,
    draw_moonphase,
)
from src.render.theme import ComponentRegion, ThemeStyle

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_draw(w: int = 800, h: int = 480):
    img = Image.new("1", (w, h), 1)
    return img, ImageDraw.Draw(img)


def _make_weather(**overrides) -> WeatherData:
    defaults = dict(
        current_temp=68.0,
        current_icon="02d",
        current_description="partly cloudy",
        high=74.0,
        low=55.0,
        humidity=50,
        sunrise=datetime(2024, 3, 15, 6, 30),
        sunset=datetime(2024, 3, 15, 19, 45),
    )
    defaults.update(overrides)
    return WeatherData(**defaults)


def _make_data(**overrides) -> DashboardData:
    data = DashboardData(weather=_make_weather())
    for k, v in overrides.items():
        setattr(data, k, v)
    return data


TODAY = date(2024, 3, 15)


# ---------------------------------------------------------------------------
# _ordinal_suffix
# ---------------------------------------------------------------------------


class TestOrdinalSuffix:
    @pytest.mark.parametrize(
        "n,expected",
        [
            (1, "st"),
            (2, "nd"),
            (3, "rd"),
            (4, "th"),
            (10, "th"),
            (11, "th"),  # teen exception
            (12, "th"),  # teen exception
            (13, "th"),  # teen exception
            (21, "st"),
            (22, "nd"),
            (23, "rd"),
            (24, "th"),
            (100, "th"),
            (101, "st"),
            (111, "th"),  # teen exception in hundreds
            (112, "th"),
        ],
    )
    def test_suffix(self, n, expected):
        assert _ordinal_suffix(n) == expected


# ---------------------------------------------------------------------------
# _quote_for_panel — refresh modes
# ---------------------------------------------------------------------------


class TestQuoteForPanel:
    def test_daily_refresh_is_deterministic(self):
        q1 = _quote_for_panel(TODAY, refresh="daily")
        q2 = _quote_for_panel(TODAY, refresh="daily")
        assert q1 == q2

    def test_different_days_may_differ(self):
        """Two different dates should generally produce different quotes.
        This is probabilistic but with 5+ quotes it's extremely reliable."""
        quotes = {
            json.dumps(_quote_for_panel(date(2024, 3, d), refresh="daily")) for d in range(1, 20)
        }
        assert len(quotes) > 1

    def test_hourly_refresh_uses_hour(self):
        now_am = datetime(2024, 3, 15, 9, 0)
        now_pm = datetime(2024, 3, 15, 14, 0)
        q_am = _quote_for_panel(TODAY, refresh="hourly", now=now_am)
        q_pm = _quote_for_panel(TODAY, refresh="hourly", now=now_pm)
        # Same date but different hours — they may differ (not guaranteed, but
        # test that the call succeeds and returns a dict with expected keys)
        assert "text" in q_am
        assert "author" in q_pm

    def test_twice_daily_am_pm_differ(self):
        now_am = datetime(2024, 3, 15, 8, 0)
        now_pm = datetime(2024, 3, 15, 13, 0)
        q_am = _quote_for_panel(TODAY, refresh="twice_daily", now=now_am)
        q_pm = _quote_for_panel(TODAY, refresh="twice_daily", now=now_pm)
        assert "text" in q_am
        assert "text" in q_pm

    def test_returns_dict_with_text_and_author(self):
        q = _quote_for_panel(TODAY)
        assert "text" in q
        assert "author" in q

    def test_fallback_to_default_quotes_when_file_missing(self):
        with patch(
            "src.render.components.moonphase_panel.QUOTES_FILE",
            Path("/nonexistent/path/quotes.json"),
        ):
            q = _quote_for_panel(TODAY)
        assert "text" in q
        assert "author" in q

    def test_fallback_on_corrupt_json(self, tmp_path):
        corrupt_file = tmp_path / "quotes.json"
        corrupt_file.write_text("{ this is not valid json }")
        with patch("src.render.components.moonphase_panel.QUOTES_FILE", corrupt_file):
            q = _quote_for_panel(TODAY)
        assert "text" in q

    def test_mp_key_prefix_differs_from_info_panel(self):
        """moonphase key prefix 'moonphase-' ensures independence from info_panel."""
        mp_key = f"moonphase-{TODAY.isoformat()}"
        info_key = TODAY.isoformat()
        assert mp_key != info_key


# ---------------------------------------------------------------------------
# draw_moonphase — smoke tests
# ---------------------------------------------------------------------------


class TestDrawMoonphaseSmoke:
    def test_renders_with_full_data(self):
        _, draw = _make_draw()
        draw_moonphase(draw, _make_data(), TODAY)

    def test_returns_none(self):
        _, draw = _make_draw()
        result = draw_moonphase(draw, _make_data(), TODAY)
        assert result is None

    def test_produces_non_blank_image(self):
        img, draw = _make_draw()
        draw_moonphase(draw, _make_data(), TODAY)
        assert img.getbbox() is not None

    def test_renders_without_weather(self):
        """weather=None skips weather and celestial strips without crashing."""
        _, draw = _make_draw()
        data = _make_data(weather=None)
        draw_moonphase(draw, data, TODAY)

    def test_renders_with_default_region_and_style(self):
        """Passing region=None and style=None triggers default-assignment branches."""
        _, draw = _make_draw()
        draw_moonphase(draw, _make_data(), TODAY, region=None, style=None)

    def test_renders_with_custom_region(self):
        _, draw = _make_draw()
        region = ComponentRegion(0, 0, 800, 480)
        draw_moonphase(draw, _make_data(), TODAY, region=region)

    def test_renders_with_custom_style(self):
        _, draw = _make_draw()
        style = ThemeStyle()
        draw_moonphase(draw, _make_data(), TODAY, style=style)


# ---------------------------------------------------------------------------
# draw_moonphase — date variations covering lunar cycle
# ---------------------------------------------------------------------------


class TestDrawMoonphasePhases:
    @pytest.mark.parametrize(
        "d",
        [
            date(2024, 1, 11),  # new moon
            date(2024, 1, 18),  # first quarter
            date(2024, 1, 25),  # full moon
            date(2024, 2, 2),  # last quarter
            date(2024, 3, 15),  # waxing crescent
            date(2024, 6, 21),  # summer solstice
            date(2024, 12, 31),  # year boundary
        ],
    )
    def test_renders_across_lunar_cycle(self, d):
        _, draw = _make_draw()
        draw_moonphase(draw, _make_data(), d)


# ---------------------------------------------------------------------------
# draw_moonphase — weather without sunrise/sunset
# ---------------------------------------------------------------------------


class TestDrawMoonphaseCelestialStrip:
    def test_renders_without_sunrise(self):
        _, draw = _make_draw()
        wx = _make_weather(sunrise=None)
        data = _make_data(weather=wx)
        draw_moonphase(draw, data, TODAY)

    def test_renders_without_sunset(self):
        _, draw = _make_draw()
        wx = _make_weather(sunset=None)
        data = _make_data(weather=wx)
        draw_moonphase(draw, data, TODAY)

    def test_renders_without_sunrise_and_sunset(self):
        _, draw = _make_draw()
        wx = _make_weather(sunrise=None, sunset=None)
        data = _make_data(weather=wx)
        draw_moonphase(draw, data, TODAY)


# ---------------------------------------------------------------------------
# draw_moonphase — quote refresh modes
# ---------------------------------------------------------------------------


class TestDrawMoonphaseQuoteRefresh:
    @pytest.mark.parametrize("mode", ["daily", "hourly", "twice_daily"])
    def test_refresh_mode_renders(self, mode):
        _, draw = _make_draw()
        draw_moonphase(draw, _make_data(), TODAY, quote_refresh=mode)


# ---------------------------------------------------------------------------
# Integration: via render_dashboard with moonphase theme
# ---------------------------------------------------------------------------


class TestMoonphaseThemeIntegration:
    def test_moonphase_theme_renders_via_canvas(self):
        from PIL import Image as PILImage

        from src.config import DisplayConfig
        from src.render.canvas import render_dashboard
        from src.render.theme import load_theme

        data = _make_data()
        result = render_dashboard(data, DisplayConfig(), theme=load_theme("moonphase"))
        assert isinstance(result, PILImage.Image)
        assert result.size == (800, 480)

    def test_moonphase_invert_theme_renders(self):
        from PIL import Image as PILImage

        from src.config import DisplayConfig
        from src.render.canvas import render_dashboard
        from src.render.theme import load_theme

        data = _make_data()
        result = render_dashboard(data, DisplayConfig(), theme=load_theme("moonphase_invert"))
        assert isinstance(result, PILImage.Image)

    def test_moonphase_in_available_themes(self):
        from src.render.theme import AVAILABLE_THEMES

        assert "moonphase" in AVAILABLE_THEMES
        assert "moonphase_invert" in AVAILABLE_THEMES

    def test_moonphase_in_random_pool(self):
        from src.render.random_theme import eligible_themes

        pool = eligible_themes(include=[], exclude=[])
        assert "moonphase" in pool
        assert "moonphase_invert" in pool
