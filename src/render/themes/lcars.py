"""LCARS theme — Star Trek computer interface aesthetic for the eInk dashboard.

Layout: left sidebar (200px) with stacked panels (weather, crew manifest, info)
separated by LCARS-style rounded pill labels.  The main 600px area holds the week
view.  A characteristic elbow cap in the top-left, a crossbar spanning the header
bottom, and a vertical connecting bar form the iconic LCARS chrome.

Visual style:
- Black canvas, white structural elements (pills, connecting bars, elbow cap).
- DM Sans for all text — clean, geometric, screen-optimised.
- White body/event text; black-on-white text on pill labels.
- Inverted today column (white fill + black text).
- Section pill labels: "STELLAR CONDITIONS", "CREW MANIFEST", "STARFLEET QUERY".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.render.fonts import dm_bold, dm_medium, dm_regular, dm_semibold
from src.render.theme import ComponentRegion, Theme, ThemeLayout, ThemeStyle

if TYPE_CHECKING:
    from PIL import ImageDraw


# ---------------------------------------------------------------------------
# Layout geometry
# ---------------------------------------------------------------------------

_CANVAS_W = 800
_CANVAS_H = 480

# Header
_HEADER_H = 55          # total header height
_HDR_BAR_H = 10         # thickness of bottom crossbar
_ELBOW_CAP_W = 155      # right edge of left header cap pill (x: 5 → 155)
_ELBOW_RADIUS = 14      # corner radius for the header cap pill

# Sidebar / vertical connecting bar
_SIDEBAR_W = 200        # total sidebar width (content + bar)
_VBAR_X = 188           # left edge of vertical connecting bar
_VBAR_W = 12            # bar width; right edge x=199, main area starts x=200

# Sidebar section label pills (x: 5 → 182, width=177)
_PILL_X = 5
_PILL_RIGHT = 182
_PILL_H = 24
_PILL_RADIUS = 5

# Section y-positions within the body (body starts at y=_HEADER_H=55)
# Layout arithmetic: 10 + 24 + 155 + 5 + 24 + 100 + 5 + 24 + 68 + 10 = 425 = 480-55 ✓
_WEATHER_PILL_Y = 65        # pill: y=65..88
_WEATHER_CONT_Y = 89        # content: y=89..243  (h=155)
_WEATHER_CONT_H = 155

_BIRTHDAY_PILL_Y = 249      # gap 5px; pill: y=249..272
_BIRTHDAY_CONT_Y = 273      # content: y=273..372 (h=100)
_BIRTHDAY_CONT_H = 100

_INFO_PILL_Y = 378          # gap 5px; pill: y=378..401
_INFO_CONT_Y = 402          # content: y=402..469 (h=68); 10px bottom margin to 480
_INFO_CONT_H = 68

# Main area (right of sidebar)
_MAIN_X = _SIDEBAR_W        # 200
_MAIN_W = _CANVAS_W - _MAIN_X  # 600

# Default pill label text (overridable via style.component_labels)
_DEFAULT_LABELS: dict[str, str] = {
    "weather": "STELLAR CONDITIONS",
    "birthdays": "CREW MANIFEST",
    "info": "STARFLEET QUERY",
}


# ---------------------------------------------------------------------------
# Overlay drawing
# ---------------------------------------------------------------------------

def _draw_lcars_overlay(
    draw: "ImageDraw.ImageDraw",
    layout: ThemeLayout,
    style: ThemeStyle,
) -> None:
    """Overlay: draws all LCARS chrome elements on top of component content."""
    W = layout.canvas_w
    H = layout.canvas_h
    fg = style.fg   # WHITE (1)
    bg = style.bg   # BLACK (0)

    # ------------------------------------------------------------------
    # 1. Header left elbow cap pill
    # ------------------------------------------------------------------
    # Clear the cap area first (component content should not reach here, but
    # resetting ensures the black gap between cap and crossbar is always clean).
    draw.rectangle([0, 0, _ELBOW_CAP_W + 5, _HEADER_H - _HDR_BAR_H - 1], fill=bg)
    draw.rounded_rectangle(
        [5, 5, _ELBOW_CAP_W, _HEADER_H - _HDR_BAR_H - 4],
        radius=_ELBOW_RADIUS,
        fill=fg,
    )

    # ------------------------------------------------------------------
    # 2. Header crossbar (thin bar at the bottom of the header strip)
    # ------------------------------------------------------------------
    draw.rectangle(
        [_MAIN_X, _HEADER_H - _HDR_BAR_H, W - 5, _HEADER_H - 1],
        fill=fg,
    )

    # ------------------------------------------------------------------
    # 3. Vertical sidebar connecting bar
    # ------------------------------------------------------------------
    draw.rectangle(
        [_VBAR_X, _HEADER_H, _VBAR_X + _VBAR_W - 1, H - 17],
        fill=fg,
    )

    # ------------------------------------------------------------------
    # 4. Bottom sidebar cap pill
    # ------------------------------------------------------------------
    draw.rounded_rectangle([5, H - 15, _ELBOW_CAP_W, H - 5], radius=6, fill=fg)

    # ------------------------------------------------------------------
    # 5. Section label pills: white pill + black centred label text
    # ------------------------------------------------------------------
    label_font = style.font_bold(9)
    pill_specs = [
        (_WEATHER_PILL_Y, "weather"),
        (_BIRTHDAY_PILL_Y, "birthdays"),
        (_INFO_PILL_Y, "info"),
    ]
    for pill_y, key in pill_specs:
        label = style.component_labels.get(key) or _DEFAULT_LABELS[key]
        pill_bottom = pill_y + _PILL_H - 1

        # White pill background
        draw.rounded_rectangle(
            [_PILL_X, pill_y, _PILL_RIGHT, pill_bottom],
            radius=_PILL_RADIUS,
            fill=fg,
        )

        # Black label text, centred on the pill
        bbox = draw.textbbox((0, 0), label, font=label_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = _PILL_X + (_PILL_RIGHT - _PILL_X - text_w) // 2
        text_y = pill_y + (_PILL_H - text_h) // 2 - bbox[1]
        draw.text((text_x, text_y), label, font=label_font, fill=bg)


# ---------------------------------------------------------------------------
# Theme factory
# ---------------------------------------------------------------------------

def lcars_theme() -> Theme:
    """Return the LCARS theme — black canvas, white LCARS chrome, DM Sans fonts."""

    layout = ThemeLayout(
        canvas_w=_CANVAS_W,
        canvas_h=_CANVAS_H,
        # Header title area sits to the right of the left elbow cap
        header=ComponentRegion(_MAIN_X, 0, _MAIN_W, _HEADER_H - _HDR_BAR_H),
        # Week view occupies the full right area below the header
        week_view=ComponentRegion(_MAIN_X, _HEADER_H, _MAIN_W, _CANVAS_H - _HEADER_H),
        # Sidebar panels: positioned below their respective LCARS pill labels
        weather=ComponentRegion(
            _PILL_X, _WEATHER_CONT_Y, _PILL_RIGHT - _PILL_X, _WEATHER_CONT_H,
        ),
        birthdays=ComponentRegion(
            _PILL_X, _BIRTHDAY_CONT_Y, _PILL_RIGHT - _PILL_X, _BIRTHDAY_CONT_H,
        ),
        info=ComponentRegion(
            _PILL_X, _INFO_CONT_Y, _PILL_RIGHT - _PILL_X, _INFO_CONT_H,
        ),
        today_view=ComponentRegion(0, 0, 0, 0, visible=False),
        draw_order=["header", "weather", "birthdays", "info", "week_view"],
        overlay_fn=_draw_lcars_overlay,
    )

    style = ThemeStyle(
        fg=1,                           # WHITE on black canvas
        bg=0,                           # BLACK background
        invert_header=False,            # header: white text on black (not a white bar)
        invert_today_col=True,          # today column: white fill + black text
        invert_allday_bars=True,        # all-day event bars: solid white
        spacing_scale=0.9,              # slightly compact for narrow sidebar panels
        label_font_size=8,
        label_font_weight="bold",
        # DM Sans — geometric, screen-optimised (same family as minimalist theme)
        font_regular=dm_regular,
        font_medium=dm_medium,
        font_semibold=dm_semibold,
        font_bold=dm_bold,
        font_title=dm_bold,
        font_date_number=dm_bold,
        font_month_title=dm_bold,
        font_section_label=dm_bold,
        # Suppress the components' built-in section labels; the overlay pills serve
        # as the sole section identifiers.
        component_labels={"weather": " ", "birthdays": " ", "info": " "},
    )

    return Theme(name="lcars", style=style, layout=layout)
