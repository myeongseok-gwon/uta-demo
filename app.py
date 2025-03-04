import os
import base64
import streamlit as st
import pandas as pd
from PIL import Image

# --- Settings ---
st.set_page_config(
    page_title="Influencer Analysis",
    layout="wide",         # Wide layout
    initial_sidebar_state="collapsed"  # Collapse sidebar by default
)

DATA_DIR = "./"  # Directory for CSV files
IMAGE_DIR = "./top_100_images"  # Directory for images
LOGO_PATH = os.path.join(DATA_DIR, "ADOASIS.png")  # Path for the logo image

# List of available brands
BRANDS = ['Lyft', 'Redbull', 'Kroger', 'Sephora', 'Nestle', 'Lululemon']

# --- Top Bar UI ---
top_bar = st.container()
with top_bar:
    # Display logo on the top left
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH)
        st.image(logo, width=150)
    else:
        st.text("Logo not found")

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Create columns for brand selector and weight slider
    col1, col2 = st.columns([2, 3])
    with col1:
        selected_brand = st.selectbox("Select Brand", BRANDS)
    with col2:
        slider_weight = st.slider("Weight for Appearance Score (remaining for Brand Fit Score)", 0.0, 1.0, 0.2, 0.1)

st.title(f"{selected_brand} Influencer Analysis")

# --- Load CSV Files ---
appearance_reasons_csv = f"top_100_{selected_brand}_appearance.csv"
appearance_reasons_path = os.path.join(DATA_DIR, appearance_reasons_csv)

meta_csv = "top_100.csv"
meta_path = os.path.join(DATA_DIR, meta_csv)

if not os.path.exists(appearance_reasons_path):
    st.error(f"File not found: {appearance_reasons_csv}")
    st.stop()

if not os.path.exists(meta_path):
    st.error(f"File not found: {meta_csv}")
    st.stop()

df_appearance_reasons = pd.read_csv(appearance_reasons_path)
df_meta = pd.read_csv(meta_path)

# Merge appearance score/reason with metadata using "influencer" as the key
df_app = pd.merge(df_appearance_reasons, df_meta, on="influencer", how="left")

# Drop rows with missing Instagram link or follower information
df_app = df_app[
    df_app['instagram'].notna() & df_app['instagram'].astype(str).str.strip().ne("") &
    df_app['last_followers'].notna() & df_app['last_followers'].astype(str).str.strip().ne("")
]

# Load Culture Fit CSV
culture_csv = "ad_suitability_results.csv"
culture_path = os.path.join(DATA_DIR, culture_csv)
if not os.path.exists(culture_path):
    st.error(f"File not found: {culture_csv}")
    st.stop()

df_culture = pd.read_csv(culture_path)
df_culture = df_culture[df_culture['brand'].str.lower() == selected_brand.lower()]

# Merge appearance data with culture fit data using "influencer" as the key
df_merged = pd.merge(
    df_app,
    df_culture[['influencer', 'score', 'reason']],
    on="influencer",
    how="left",
    suffixes=("_appearance", "_culture")
)

# Rename columns for clarity
df_merged.rename(columns={
    "score_appearance": "appearance_score",
    "score_culture": "culture_fit_score",
    "reason_appearance": "appearance_reason",
    "reason_culture": "culture_fit_reason"
}, inplace=True)

# Convert followers to integer with comma formatting
def to_int_str(x):
    try:
        return f"{int(float(x)):,}"
    except Exception:
        return "N/A"

df_merged['Followers'] = df_merged['last_followers'].apply(to_int_str)

# Calculate total score: total_score = slider_weight * appearance_score + (1 - slider_weight) * culture_fit_score
df_merged['appearance_score'] = pd.to_numeric(df_merged['appearance_score'], errors='coerce')
df_merged['culture_fit_score'] = pd.to_numeric(df_merged['culture_fit_score'], errors='coerce')
df_merged['total_score'] = df_merged.apply(
    lambda row: slider_weight * row['appearance_score'] + (1 - slider_weight) * row['culture_fit_score']
    if pd.notna(row['appearance_score']) and pd.notna(row['culture_fit_score'])
    else None, axis=1
)

# Sort by total_score in descending order
df_merged.sort_values(by='total_score', ascending=False, inplace=True)

# Format scores to three decimal places
df_merged['appearance_score'] = df_merged['appearance_score'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")
df_merged['culture_fit_score'] = df_merged['culture_fit_score'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")
df_merged['total_score'] = df_merged['total_score'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")

# Function to encode image to HTML <img> tag using base64
def image_to_html(image_path, width=50):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f'<img src="data:image/jpeg;base64,{encoded}" style="width:{width}px;">'
    else:
        return "No Image"

# Create Photo column (image width = 50px)
df_merged['Photo'] = df_merged['influencer'].apply(
    lambda name: image_to_html(os.path.join(IMAGE_DIR, f"{name}.jpg"), width=50)
)

# Add Instagram URL link to the influencer name
df_merged['Influencer'] = df_merged.apply(
    lambda row: f'<a href="{row["instagram"]}" target="_blank">{row["influencer"]}</a>',
    axis=1
)

# Set final columns to display (including Category and the Reason columns)
columns = ['Photo', 'Influencer', 'category', 'Followers', 'appearance_score', 'culture_fit_score', 'total_score', 'appearance_reason', 'culture_fit_reason']
col_rename = {
    'appearance_score': 'Appearance Score',
    'culture_fit_score': 'Brand Fit Score',
    'total_score': 'Total Score',
    'category': 'Category',
    'appearance_reason': 'Appearance Reason',
    'culture_fit_reason': 'Brand Fit Reason'
}

df_display = df_merged[columns].rename(columns=col_rename)

# Generate HTML table (with escape=False to render image HTML)
html_table = df_display.to_html(escape=False, index=False)
additional_css = """
<style>
    th {
        text-align: center;
    }
</style>
"""
html_table = additional_css + html_table

st.markdown(html_table, unsafe_allow_html=True)