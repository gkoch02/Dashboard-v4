"""Tests for AQI card rendering in the weather_full component."""

from datetime import date, datetime, timedelta

from PIL import Image, ImageDraw

from src.data.models import AirQualityData, DayForecast, WeatherData
from src.render.components.weather_full import draw_weather_full
from src.render.theme import ComponentRegion, ThemeStyle

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_draw(w: int = 800, h: int = 480):
    img = Image.new("1", (w, h), 1)
    return img, ImageDraw.Draw(img)


def _make_weather() -> WeatherData:
    return WeatherData(
        current_temp=72.0,
        current_icon="01d",
        current_description="clear sky",
        high=78.0,
        low=60.0,
        humidity=45,
        forecast=[
            DayForecast(
                date=date(2024, 3, 16) + timedelta(days=i),
                high=58.0 + i * 2,
                low=42.0 + i,
                icon="02d",
                description="partly cloudy",
            )
            for i in range(5)
        ],
        feels_like=70.0,
        wind_speed=5.0,
        wind_deg=315.0,
        uv_index=3.0,
        sunrise=datetime(2024, 3, 15, 6, 24),
        sunset=datetime(2024, 3, 15, 19, 45),
    )


def _make_aqi(**overrides) -> AirQualityData:
    defaults = dict(aqi=42, category="Good", pm25=9.8, pm10=14.2, sensor_id=99999)
    defaults.update(overrides)
    return AirQualityData(**defaults)


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


class TestDrawWeatherFullAqi:
    def test_renders_without_aqi(self):
        """4-card layout still works when air_quality is None."""
        img, draw = _make_draw()
        weather = _make_weather()
        # Should not raise
        draw_weather_full(draw, weather, date(2024, 3, 15), air_quality=None)

    def test_renders_with_aqi_good(self):
        """5th AQI card renders without error for a 'Good' reading."""
        img, draw = _make_draw()
        weather = _make_weather()
        aq = _make_aqi(aqi=42, category="Good")
        draw_weather_full(draw, weather, date(2024, 3, 15), air_quality=aq)

    def test_renders_with_aqi_unhealthy_for_sensitive(self):
        """Long category label is truncated to fit the card."""
        img, draw = _make_draw()
        weather = _make_weather()
        aq = _make_aqi(aqi=120, category="Unhealthy for Sensitive Groups", pm25=40.0)
        draw_weather_full(draw, weather, date(2024, 3, 15), air_quality=aq)

    def test_renders_with_aqi_hazardous(self):
        img, draw = _make_draw()
        weather = _make_weather()
        aq = _make_aqi(aqi=300, category="Very Unhealthy", pm25=200.0)
        draw_weather_full(draw, weather, date(2024, 3, 15), air_quality=aq)

    def test_renders_with_none_weather(self):
        """Unavailable fallback still works with air_quality provided."""
        img, draw = _make_draw()
        draw_weather_full(draw, None, date(2024, 3, 15), air_quality=_make_aqi())

    def test_renders_with_custom_region(self):
        img, draw = _make_draw()
        weather = _make_weather()
        region = ComponentRegion(0, 0, 800, 480)
        style = ThemeStyle()
        draw_weather_full(draw, weather, air_quality=_make_aqi(), region=region, style=style)

    def test_renders_without_pm10(self):
        """pm10=None is handled gracefully."""
        img, draw = _make_draw()
        weather = _make_weather()
        aq = _make_aqi(pm10=None)
        draw_weather_full(draw, weather, date(2024, 3, 15), air_quality=aq)
