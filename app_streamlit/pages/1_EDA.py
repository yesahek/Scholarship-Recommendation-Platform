import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app_streamlit.utils import initialize_workspace

# Initialize workspace path and imports
initialize_workspace()

# Page configuration
st.set_page_config(
    page_title="EDA - Scholarship Analysis",
    page_icon="📊",
    layout="wide"
)

# Load global CSS
try:
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles", "app.css")
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.title("Exploratory Data Analysis Scholarships")

# --- Initialize session state for scholarship data ---
if "scholarships_df" not in st.session_state:
    st.session_state.scholarships_df = None

if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

@st.cache_data
def load_scholarship_data():
    """
    Load scholarship data from workspace.
    Tries multiple sources: CSV, cleaned JSON, combined JSON.
    Returns a pandas DataFrame or None if no data is found.
    """
    workspace_path = st.session_state.get("workspace_path")
    if workspace_path:
        # 1. Try loading from CSV
        data_path = os.path.join(workspace_path, "Data", "Scholarships_data.csv")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            return df

        # 2. Try loading from cleaned_scholarships.json
        json_path = os.path.join(workspace_path, "Data", "cleaned_scholarships.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            return df

        # 3. Try loading from combined_scholarships.json
        json_path = os.path.join(workspace_path, "Data", "combined_scholarships.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            return df

    # If nothing found, return None
    return None

# Add some spacing and better intro
st.markdown("""
<div style="margin-bottom: 2rem;">
    <p style="color: #6b7280; font-size: 1.1rem; line-height: 1.6;">
        Explore comprehensive insights from global scholarship opportunities. Analyze provider trends, eligibility distributions,
        deadlines, and benefits to make informed academic and financial decisions.
    </p>
</div>
""", unsafe_allow_html=True)

# Tabs for different analyses
tab1, tab2, tab3 = st.tabs([
    "Load Scholarship Data",
    "Scholarship Overview",
    "Providers & Deadlines"
])

with tab1:
    st.markdown("### Load Scholarship Dataset")
    st.markdown("Import your scholarship opportunities data to begin analysis.")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Load Scholarship Data", type="primary"):
            with st.spinner("Loading scholarship data..."):
                try:
                    df = load_scholarship_data()
                    if df is not None:
                        st.session_state.scholarships_df = df
                        st.session_state.data_loaded = True
                        st.success(f"✅ Successfully loaded {len(df):,} scholarship records")
                        st.rerun()
                    else:
                        st.error("❌ Could not find scholarship data. Please ensure data files exist in workspace/Data/")
                except Exception as e:
                    st.error(f"❌ Error loading data: {e}")

    with col2:
        if st.session_state.data_loaded and st.session_state.scholarships_df is not None:
            df = st.session_state.scholarships_df
            st.success(f"✅ Dataset ready: {len(df):,} scholarships loaded")

    if st.session_state.data_loaded and st.session_state.scholarships_df is not None:
        df = st.session_state.scholarships_df

        # Key metrics in a nice grid
        st.markdown("### Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Scholarships", f"{len(df):,}")
        with col2:
            if 'Provider' in df.columns:
                st.metric("Providers", f"{df['Provider'].nunique():,}")
        with col3:
            if 'Country' in df.columns:
                st.metric("Countries", f"{df['Country'].nunique():,}")
        with col4:
            if 'Program' in df.columns:
                st.metric("Programs", f"{df['Program'].nunique():,}")

        # Sample data preview
        st.markdown("### Data Preview")
        st.dataframe(df.head(10), use_container_width=True)

        # Column information
        with st.expander("📋 Column Information"):
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.astype(str),
                'Non-Null Count': df.count(),
                'Null Count': df.isnull().sum(),
                'Unique Values': df.nunique()
            })
            st.dataframe(col_info, use_container_width=True)

        # Data quality summary
        with st.expander("🔍 Data Quality Summary"):
            st.markdown("#### Missing Values Overview")
            missing_data = df.isnull().sum()
            missing_percent = (missing_data / len(df)) * 100
            missing_df = pd.DataFrame({
                'Missing Count': missing_data,
                'Missing %': missing_percent.round(2)
            })
            st.dataframe(missing_df[missing_df['Missing Count'] > 0], use_container_width=True)

            st.markdown("#### Duplicate Rows")
            duplicates = df.duplicated().sum()
            st.metric("Duplicate Rows", duplicates)

with tab2:
    st.markdown("### Scholarship Overview")

    if not st.session_state.data_loaded:
        st.info("📌 Please load the dataset first from the 'Load Scholarship Data' tab.")
    else:
        df = st.session_state.scholarships_df

        # Scholarship timeline (based on deadlines or announcement dates)
        if 'Deadline' in df.columns or 'Date Announced' in df.columns:
            st.markdown("#### Scholarship Timeline")
            date_col = 'Deadline' if 'Deadline' in df.columns else 'Date Announced'
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                # Group by month for smoother trends
                df['Month'] = df[date_col].dt.to_period('M')
                date_counts = df['Month'].value_counts().sort_index()

                fig = px.line(
                    x=date_counts.index.astype(str),
                    y=date_counts.values,
                    labels={'x': 'Month', 'y': 'Number of Scholarships'},
                    title='Scholarships Over Time'
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not parse dates: {e}")

        # Top scholarship programs (split multiple values)
        if 'Program' in df.columns:
            df['Program'] = df['Program'].astype(str)
            program_split = df['Program'].str.split(',').explode().str.strip()
            top_programs = program_split.value_counts().head(20)

            fig = px.bar(
                x=top_programs.values,
                y=top_programs.index,
                orientation='h',
                labels={'x': 'Number of Scholarships', 'y': 'Program'},
                title='Top 20 Scholarship Programs'
            )
            fig.update_traces(hoverinfo='none')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
            st.plotly_chart(fig, use_container_width=True)

        # Eligibility text length analysis
        if 'Eligibility Length' in df.columns or 'Eligibility' in df.columns:
            st.markdown("#### Eligibility Text Analysis")
            if 'Eligibility Length' not in df.columns and 'Eligibility' in df.columns:
                df['Eligibility Length'] = df['Eligibility'].astype(str).str.len()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Eligibility Length", f"{df['Eligibility Length'].mean():.0f} chars")
            with col2:
                st.metric("Median Eligibility Length", f"{df['Eligibility Length'].median():.0f} chars")
            with col3:
                st.metric("Max Eligibility Length", f"{df['Eligibility Length'].max():.0f} chars")

            fig = px.histogram(
                df,
                x='Eligibility Length',
                nbins=50,
                title='Distribution of Eligibility Text Lengths'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Word count analysis
            if 'Eligibility' in df.columns:
                df['Word Count'] = df['Eligibility'].astype(str).str.split().str.len()
                fig2 = px.histogram(
                    df,
                    x='Word Count',
                    nbins=50,
                    title='Distribution of Word Counts in Eligibility Texts'
                )
                st.plotly_chart(fig2, use_container_width=True)
with tab3:
    st.markdown("### Scholarship Provider & Location Analysis")

    if not st.session_state.data_loaded:
        st.info("📌 Please load the dataset first from the 'Load Scholarship Data' tab.")
    else:
        df = st.session_state.scholarships_df

        # Top scholarship providers
        if 'Provider' in df.columns:
            top_providers = df['Provider'].value_counts().head(20)

            fig = px.bar(
                x=top_providers.values,
                y=top_providers.index,
                orientation='h',
                labels={'x': 'Number of Scholarships', 'y': 'Provider'},
                title='Top 20 Scholarship Providers'
            )
            fig.update_traces(hoverinfo='none')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
            st.plotly_chart(fig, use_container_width=True)

        # Location analysis (adapted to Country column)
        if 'Country' in df.columns:
            st.markdown("#### Top Scholarship Countries")
            top_countries = df['Country'].value_counts().head(15)

            fig = px.bar(
                x=top_countries.values,
                y=top_countries.index,
                orientation='h',
                labels={'x': 'Number of Scholarships', 'y': 'Country'},
                title='Top 15 Scholarship Countries'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        # Insights analysis (optional, only if you add an Insights column)
        if 'Insights' in df.columns:
            st.markdown("#### Scholarship Insights Distribution")
            all_insights = []
            for insights in df['Insights'].dropna():
                if isinstance(insights, str):
                    all_insights.extend(insights.split(','))

            if all_insights:
                insight_counts = Counter([i.strip() for i in all_insights])
                insight_df = pd.DataFrame.from_dict(insight_counts, orient='index', columns=['Count'])
                insight_df = insight_df.sort_values('Count', ascending=False).head(50)

                fig = px.bar(
                    insight_df,
                    x=insight_df.index,
                    y='Count',
                    title='Top Scholarship Insights',
                    labels={'x': 'Insight', 'y': 'Count'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)