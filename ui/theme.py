"""
OmniFHIR-AI Streamlit UI Theme — Cotiviti brand-aligned styling.

Provides CSS injection and color constants for the Streamlit interface.
"""

# ─── Cotiviti Brand Color Palette ────────────────────────────────────────────
COLORS = {
    "primary": "#2D1A4E",        # Deep purple — headers, nav
    "primary_light": "#4A3170",  # Lighter purple
    "accent": "#E91E8C",         # Magenta/pink — CTAs, highlights
    "accent_light": "#F472B6",   # Lighter magenta
    "secondary": "#00B4D8",      # Teal — links, info indicators
    "secondary_light": "#67E8F9",# Lighter teal
    "success": "#10B981",        # Green — COMPLIANT
    "success_bg": "#D1FAE5",     # Light green background
    "danger": "#EF4444",         # Red — NON-COMPLIANT
    "danger_bg": "#FEE2E2",      # Light red background
    "warning": "#F59E0B",        # Amber — low confidence
    "warning_bg": "#FEF3C7",     # Light amber background
    "bg": "#F8F9FA",             # Page background
    "card_bg": "#FFFFFF",        # Card background
    "text_primary": "#1F2937",   # Main text
    "text_secondary": "#6B7280", # Muted text
    "border": "#E5E7EB",        # Borders
    "border_light": "#F3F4F6",  # Subtle borders
}


def get_custom_css() -> str:
    """Return the complete custom CSS for the Streamlit app."""
    return f"""
    <style>
        /* ── Global Styles ─────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        .stApp {{
            font-family: 'Inter', sans-serif;
        }}

        /* ── Header Banner ─────────────────────────────────────────── */
        .main-header {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_light']} 50%, {COLORS['accent']} 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(45, 26, 78, 0.3);
        }}

        .main-header h1 {{
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}

        .main-header p {{
            margin: 0.3rem 0 0 0;
            font-size: 0.95rem;
            opacity: 0.9;
        }}

        /* ── Metric Cards ──────────────────────────────────────────── */
        .metric-card {{
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 1.2rem;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {COLORS['primary']};
            line-height: 1;
        }}

        .metric-label {{
            font-size: 0.8rem;
            font-weight: 500;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 0.3rem;
        }}

        /* ── Status Badges ─────────────────────────────────────────── */
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}

        .badge-compliant {{
            background: {COLORS['success_bg']};
            color: {COLORS['success']};
        }}

        .badge-non-compliant {{
            background: {COLORS['danger_bg']};
            color: {COLORS['danger']};
        }}

        .badge-pending {{
            background: {COLORS['warning_bg']};
            color: {COLORS['warning']};
        }}

        .badge-approved {{
            background: {COLORS['success_bg']};
            color: {COLORS['success']};
        }}

        .badge-rejected {{
            background: {COLORS['danger_bg']};
            color: {COLORS['danger']};
        }}

        .badge-flagged {{
            background: {COLORS['warning_bg']};
            color: {COLORS['warning']};
        }}

        .badge-failed {{
            background: {COLORS['danger_bg']};
            color: {COLORS['danger']};
        }}

        /* ── Confidence Indicator ──────────────────────────────────── */
        .confidence-high {{
            color: {COLORS['success']};
            font-weight: 600;
        }}

        .confidence-medium {{
            color: {COLORS['warning']};
            font-weight: 600;
        }}

        .confidence-low {{
            color: {COLORS['danger']};
            font-weight: 600;
        }}

        /* ── Detail View Panels ────────────────────────────────────── */
        .panel {{
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 1.2rem;
            height: 100%;
        }}

        .panel-header {{
            font-size: 0.85rem;
            font-weight: 600;
            color: {COLORS['primary']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding-bottom: 0.6rem;
            margin-bottom: 0.8rem;
            border-bottom: 2px solid {COLORS['accent']};
        }}

        /* ── Provenance Timeline ───────────────────────────────────── */
        .timeline-item {{
            display: flex;
            align-items: flex-start;
            padding: 0.6rem 0;
            border-left: 2px solid {COLORS['border']};
            padding-left: 1rem;
            margin-left: 0.5rem;
        }}

        .timeline-item.success {{
            border-left-color: {COLORS['success']};
        }}

        .timeline-item.failure {{
            border-left-color: {COLORS['danger']};
        }}

        .timeline-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 0.5rem;
            margin-top: 0.3rem;
            flex-shrink: 0;
        }}

        .dot-success {{
            background: {COLORS['success']};
        }}

        .dot-failure {{
            background: {COLORS['danger']};
        }}

        /* ── FHIR JSON Display ─────────────────────────────────────── */
        .fhir-json {{
            background: #1a1b26;
            color: #c0caf5;
            border-radius: 8px;
            padding: 1rem;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.78rem;
            line-height: 1.5;
            overflow-x: auto;
            max-height: 500px;
            overflow-y: auto;
        }}

        /* ── Action Buttons ────────────────────────────────────────── */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 600;
            letter-spacing: 0.3px;
            transition: all 0.2s ease;
        }}

        /* ── Data Table Styling ─────────────────────────────────────── */
        .stDataFrame {{
            border-radius: 10px;
            overflow: hidden;
        }}

        /* ── Hide Streamlit Defaults ───────────────────────────────── */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
    """


def render_badge(text: str, badge_type: str = "pending") -> str:
    """Render an HTML badge for status display.

    Args:
        text: The badge text.
        badge_type: One of: compliant, non-compliant, pending, approved, rejected, flagged, failed.

    Returns:
        HTML string for the badge.
    """
    css_class = f"badge-{badge_type.lower().replace('_', '-').replace(' ', '-')}"
    return f'<span class="badge {css_class}">{text}</span>'


def render_confidence(score: float) -> str:
    """Render a confidence score with color-coded styling.

    Args:
        score: Confidence score between 0.0 and 1.0.

    Returns:
        HTML string with styled confidence display.
    """
    if score is None:
        return '<span class="confidence-low">N/A</span>'

    if score >= 0.8:
        css_class = "confidence-high"
    elif score >= 0.5:
        css_class = "confidence-medium"
    else:
        css_class = "confidence-low"

    return f'<span class="{css_class}">{score:.0%}</span>'


def render_metric_card(value: str, label: str) -> str:
    """Render a dashboard metric card.

    Args:
        value: The metric value to display.
        label: The metric label.

    Returns:
        HTML string for the metric card.
    """
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """
