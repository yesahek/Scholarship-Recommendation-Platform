import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import json
import unicodedata
import re
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app_streamlit.utils import initialize_workspace

# Initialize workspace path and imports
initialize_workspace()

st.set_page_config(
    page_title="Data Cleaning - Scholarship Analysis",
    page_icon="🧹",
    layout="wide"
)

st.title("Data Cleaning - Scholarship Analysis")
st.markdown("Clean and preprocess scholarship datasets for accurate analysis.")

# Load global CSS
try:
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles", "app.css")
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

# Initialize session state
if 'raw_scholarships_df' not in st.session_state:
    st.session_state.raw_scholarships_df = None
if 'cleaned_scholarships_df' not in st.session_state:
    st.session_state.cleaned_scholarships_df = None

def build_scholarship_text(row):
    """Combine scholarship info into one text block"""
    parts = []
    if pd.notnull(row.get("Scholarship Name")):
        parts.append("Scholarship Name:\n" + str(row["Scholarship Name"]))
    if pd.notnull(row.get("Provider")):
        parts.append("Provider:\n" + str(row["Provider"]))
    if pd.notnull(row.get("Country")):
        parts.append("Country:\n" + str(row["Country"]))
    if pd.notnull(row.get("Eligibility")):
        parts.append("Eligibility:\n" + str(row["Eligibility"]))
    if pd.notnull(row.get("Benefits")):
        parts.append("Benefits:\n" + str(row["Benefits"]))
    if pd.notnull(row.get("Program")):
        parts.append("Program:\n" + str(row["Program"]))
    if pd.notnull(row.get("Deadline")):
        parts.append("Deadline:\n" + str(row["Deadline"]))
    if pd.notnull(row.get("Application Link")):
        parts.append("Application Link:\n" + str(row["Application Link"]))
    return "\n".join(parts)

def clean_scholarship_text(text):
    """Clean scholarship text: remove emails, URLs, HTML, normalize bullets"""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", text)
    text = re.sub(r"\S+@\S+", " ", text)                          # emails
    text = re.sub(r"\+?\d[\d\-\s\(\)]{7,}\d", " ", text)          # phone numbers
    text = re.sub(r"(https?:\/\/\S+|www\.\S+)", " ", text)        # URLs
    text = re.sub(r"<[^>]+>", " ", text)                          # HTML tags
    text = re.sub(r"&[a-z]+;", " ", text)                         # HTML entities
    text = re.sub(r"[•●▪■◆▶►▸⦿⦾]", "- ", text)                   # bullets
    text = text.replace("–", "-").replace("—", "-")               # dashes
    text = text.replace("\t", " ")
    text = re.sub(r" {2,}", " ", text)
    lines = [line.strip() for line in text.split("\n")]
    final_lines, blank_seen = [], False
    for line in lines:
        if line == "":
            if not blank_seen:
                final_lines.append("")
            blank_seen = True
        else:
            final_lines.append(line)
            blank_seen = False
    text = "\n".join(final_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def load_raw_scholarship_data():
    """Load raw scholarship data from workspace"""
    workspace_path = st.session_state.get('workspace_path')
    if workspace_path:
        possible_paths = [
            os.path.join(workspace_path, "Data", "Scholarships_data.csv"),
            os.path.join(workspace_path, "Data_Cleaning", "Scholarships_data.csv"),
            os.path.join(workspace_path, "scraps", "combined_scholarships.json"),
            os.path.join(workspace_path, "combined_scholarships.json")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    if path.endswith('.csv'):
                        df = pd.read_csv(path)
                    elif path.endswith('.json'):
                        with open(path, 'r') as f:
                            data = json.load(f)
                        df = pd.DataFrame(data)
                    st.success(f"✅ Loaded raw data from {path}")
                    return df
                except Exception as e:
                    st.warning(f"Failed to load {path}: {e}")
                    continue
    st.error("❌ Could not find raw scholarship data files")
    return None

# Main interface
st.markdown("### Clean and Process Scholarship Data")
st.markdown("""
This page allows you to:
- Load raw scholarship data
- Apply comprehensive text cleaning
- Remove duplicates
- Save cleaned data to JSON/CSV format
""")

# Load raw data
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Load Raw Scholarship Data", type="primary"):
        with st.spinner("Loading raw scholarship data..."):
            df = load_raw_scholarship_data()
            if df is not None:
                st.session_state.raw_scholarships_df = df
                st.session_state.cleaned_scholarships_df = None
                st.rerun()

with col2:
    st.button("Clear Loaded Data", on_click=lambda: clear_data())

def clear_data():
    st.session_state.raw_scholarships_df = None
    st.session_state.cleaned_scholarships_df = None
    st.rerun()

# Display raw data info
if st.session_state.raw_scholarships_df is not None:
    df = st.session_state.raw_scholarships_df
    st.success(f"✅ Raw data loaded: {len(df):,} scholarships")

    # Data overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Scholarships", f"{len(df):,}")
    with col2:
        duplicate_count = df.duplicated().sum()
        st.metric("Duplicate Rows", duplicate_count)
    with col3:
        missing_text = df.get('Eligibility', pd.Series()).isnull().sum()
        st.metric("Missing Eligibility", missing_text)

    # Cleaning options
    st.markdown("### Cleaning Options")
    col1, col2 = st.columns(2)
    with col1:
        add_scholarship_id = st.checkbox("Add scholarship_id column", value=True)
        combine_text = st.checkbox("Combine multiple text columns", value=True)
    with col2:
        clean_text = st.checkbox("Apply text cleaning", value=True)
        deduplicate_on_text = st.checkbox("Deduplicate on cleaned text", value=True,
                                          help="Remove duplicates based on cleaned text only")

    # Clean data button
    if st.button("Apply Cleaning", type="primary"):
        with st.spinner("Cleaning data..."):
            cleaned_df = df.copy()
            if combine_text:
                cleaned_df['scholarship_text_raw'] = cleaned_df.apply(build_scholarship_text, axis=1)
                st.info("Combined text into 'scholarship_text_raw'")
            if clean_text:
                text_col = 'scholarship_text_raw' if 'scholarship_text_raw' in cleaned_df.columns else 'Eligibility'
                if text_col in cleaned_df.columns:
                    cleaned_df['scholarship_text_cleaned'] = cleaned_df[text_col].apply(clean_scholarship_text)
                    st.info("Applied text cleaning to create 'scholarship_text_cleaned'")
            if deduplicate_on_text and 'scholarship_text_cleaned' in cleaned_df.columns:
                initial_count = len(cleaned_df)
                cleaned_df = cleaned_df.drop_duplicates(subset=['scholarship_text_cleaned'], keep='first')
                st.info(f"Deduplicated: reduced from {initial_count:,} to {len(cleaned_df):,} unique scholarships")
            if add_scholarship_id:
                cleaned_df['scholarship_id'] = range(len(cleaned_df))
                st.info("Added scholarship_id column")
            st.session_state.cleaned_scholarships_df = cleaned_df
            st.success(f"✅ Cleaning complete! Processed {len(cleaned_df)} scholarships")
            st.rerun()

# Display cleaned
# Display cleaned data
if st.session_state.cleaned_scholarships_df is not None:
    cleaned_df = st.session_state.cleaned_scholarships_df

    st.markdown("### Cleaned Data Preview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cleaned Scholarships", f"{len(cleaned_df):,}")
    with col2:
        if 'scholarship_text_cleaned' in cleaned_df.columns:
            avg_length = cleaned_df['scholarship_text_cleaned'].str.len().mean()
            st.metric("Avg Text Length", f"{avg_length:.0f} chars")
    with col3:
        raw_df = st.session_state.get('raw_scholarships_df')
        if raw_df is not None:
            columns_added = len(cleaned_df.columns) - len(raw_df.columns)
            st.metric("Columns Added", columns_added)
        else:
            st.metric("Columns Added", "N/A")

    # Show sample
    st.dataframe(cleaned_df.head(10), use_container_width=True)

    # Save options
    st.markdown("### Save Cleaned Data")

    col1, col2 = st.columns(2)
    with col1:
        filename = st.text_input("Filename", value="cleaned_scholarships.json", help="Filename for saved data")

    with col2:
        save_format = st.selectbox("Format", ["JSON", "CSV"], index=0)

    if st.button("Save Cleaned Data", type="primary"):
        workspace_path = st.session_state.get('workspace_path')
        if workspace_path:
            if save_format == "JSON":
                save_path = os.path.join(workspace_path, "Data", filename)
                # Convert to records format for JSON
                json_data = cleaned_df.to_dict('records')
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

                save_path_10 = os.path.join(workspace_path, "Data", "cleaned_scholarships_sample.json")
                json_data_10 = cleaned_df.head(10).to_dict('records')
                with open(save_path_10, 'w', encoding='utf-8') as f:
                    json.dump(json_data_10, f, indent=2, ensure_ascii=False)
            else:  # CSV
                save_path = os.path.join(workspace_path, "Data", filename)
                cleaned_df.to_csv(save_path, index=False)

            st.success(f"✅ Saved {len(cleaned_df)} cleaned scholarships to {save_path}")

            # Also update combined_scholarships.json if that's the target
            if filename == "combined_scholarships.json":
                st.info("Updated combined_scholarships.json - this will be used by other pages")
        else:
            st.error("Workspace path not found")

# Footer
st.markdown("---")
st.markdown("""
**Cleaning Process:**
1. **Load Raw Data**: Import scholarships from CSV or JSON files
2. **Remove Duplicates**: Eliminate duplicate entries
3. **Combine Text**: Merge relevant columns into comprehensive scholarship descriptions
4. **Text Cleaning**: Remove noise, normalize formatting, clean HTML/entities
5. **Save Results**: Export cleaned data in JSON/CSV format for use by other analysis pages
""")