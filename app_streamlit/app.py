import streamlit as st
import  os
import base64

from utils import initialize_workspace

# Initialize workspace path and imports
initialize_workspace()

st.set_page_config(
    layout="wide",
    page_title="Scholarship Intelligence Platform",
    initial_sidebar_state="expanded"
)

try:
    css_path = os.path.join(os.path.dirname(__file__), "styles", "app.css")
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass
# CSS is loaded from styles/app.css


# Override with requested hard-coded benchmark numbers
total_scholarships = 000000
unique_providers = 00000
unique_programs = 00000

# Build metrics list using available values, fallback to defaults when missing
metrics_data = [
    {
        "label": "Scholarships Analyzed",
        "value": (f"{total_scholarships:,}" if total_scholarships not in (None, 0) else "0"),
        "delta": "",
        "context": "",
    },
    {
        "label": "Unique Providers",
        "value": (f"{unique_providers:,}" if unique_providers not in (None, 0) else "0"),
        "delta": "",
        "context": "",
    },
    {
        "label": "Unique Programs",
        "value": (f"{unique_programs:,}" if unique_programs not in (None, 0) else "0"),
        "delta": "",
        "context": "",
    },
]

# persist to session for smoother navigation
st.session_state['home_metrics'] = {'overview': metrics_data}

session_metrics = st.session_state.get("home_metrics") if "home_metrics" in st.session_state else None
if isinstance(session_metrics, list) and session_metrics:
    metrics_data = session_metrics
elif isinstance(session_metrics, dict):
    overview_metrics = session_metrics.get("overview")
    if isinstance(overview_metrics, list) and overview_metrics:
        metrics_data = overview_metrics

metric_cards = []
for metric in metrics_data:
    label = str(metric.get("label", "")).strip()
    value = str(metric.get("value", "")).strip()
    delta_text = str(metric.get("delta", "")).strip()
    context_text = str(metric.get("context", "")).strip()

    trend_html = ""
    if delta_text:
        trend_class = "trend-up" if delta_text.startswith("+") else "trend-down"
        trend_icon = "↑" if delta_text.startswith("+") else "↓"
        trend_html = f'<span class="{trend_class}">{trend_icon} {delta_text}</span>'

    metric_cards.append(
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        # f'<div class="metric-trend">{trend_html} <span style="opacity: 0.7">{context_text}</span></div>'
        f'</div>'
    )

hero_html = f"""
<div class="hero-container">
    <div class="hero-bg-pattern"></div>
    <div class="hero-content">
        <div>
            <h1 class="hero-title">AI-Powered Scholarship Intelligence</h1>
            <p class="hero-description">
                Transform how you discover and match scholarships. Our advanced AI platform uses natural language processing to uncover opportunities tailored to student profiles.
            </p>
        </div>
        <div class="metrics-grid" style="display: flex; flex-direction: column; gap: 1rem; align-items: stretch;">
            {''.join(metric_cards)}
        </div>
    </div>
</div>
"""

st.markdown(hero_html, unsafe_allow_html=True)

navigation_cards = [
    {
        "title": "Scholarship Analysis",
        "description": "Visualize scholarship trends, providers, and eligibility distributions across programs.",
        "button": "Explore Scholarships",
        "page": "pages/1_EDA.py",
        "key": "nav_scholarship_eda_btn",
    },
    {
        "title": "NLP Analytics",
        "description": "Extract keywords, eligibility criteria, and benefits from scholarship descriptions using NLP.",
        "button": "Run Analytics",
        "page": "pages/3_NLP_Analytics.py",
        "key": "nav_scholarship_analytics_btn",
    },
    {
        "title": "Profile Matching",
        "description": "Find scholarships that best match student profiles using AI-powered compatibility scoring.",
        "button": "Match Profile",
        "page": "pages/7_Profile_Matching.py",
        "key": "nav_scholarship_matching_btn",
    },
]

nav_columns = st.columns(len(navigation_cards))
for column, card in zip(nav_columns, navigation_cards):
    with column:
        st.markdown(
            f"""
            <div class="nav-card">
                <h4 class="nav-title">{card['title']}</h4>
                <p class="nav-desc">{card['description']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Button outside the card div to work with Streamlit's native button
        if st.button(card["button"], key=card["key"]):
            st.switch_page(card["page"])
