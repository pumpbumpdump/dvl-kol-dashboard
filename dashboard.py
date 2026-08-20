import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime
import re

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="Darya Vario Laboratoria KOL Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============ CUSTOM COLORS ============
DARK_BLUE = "#1a3a5c"
LIGHT_BLUE = "#4a90d9"

# ============ SIDEBAR WITH LOGO (TOP) ============
with st.sidebar:
    try:
        st.image("dvl-logo-transparent.png", use_container_width=True)
    except:
        st.markdown(f"""
        <div style="display: flex; justify-content: center; font-size: 60px; color: {DARK_BLUE};">
            📊
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: center; color: {DARK_BLUE}; font-size: 18px; font-weight: bold; margin-bottom: 20px;">
        Darya Vario Laboratoria<br>KOL Dashboard
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()

# ============ LOAD DATA ============
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Union Data KOL.csv', sep=';', encoding='latin-1')
        return df
    except:
        try:
            df = pd.read_csv('Union Data KOL.csv', sep=';', encoding='utf-8')
            return df
        except:
            st.error("❌ Could not load the file")
            st.info("Make sure 'Union Data KOL.csv' is in the folder")
            return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# ============ CLEAN COLUMN NAMES ============
df.columns = [str(col).strip().replace(' ', '_').replace('/', '_').replace('-', '_').replace('(', '').replace(')', '') for col in df.columns]

# ============ CONVERT DATA TYPES ============
numeric_cols = ['Followers_Number', 'Actual_Spends_IDR', 'Reach', 'Views', 'Likes', 'Comments', 'Share', 'ER', 'ER_Views', 'VR', 'CPV_Rp']
for col in numeric_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce')

# ============ FIX: CLEAN AND VALIDATE MONTHS ============
if 'Month' in df.columns:
    df['Month'] = df['Month'].astype(str).str.strip()
    valid_months = ['Jan-26', 'Feb-26', 'Mar-26', 'Apr-26', 'May-26', 'Jun-26', 'Jul-26']
    df = df[df['Month'].isin(valid_months)]
    df['Month'] = pd.to_datetime(df['Month'], format='%b-%y')

# ============ SIDEBAR FILTERS (WITH SORTED MONTHS) ============
with st.sidebar:
    st.subheader("Filters")
    
    filtered_df = df.copy()
    
    # Filter by Month - FIXED SORTING
    if 'Month' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Month']):
        # Sort the unique months chronologically before creating the dropdown list
        sorted_months = sorted(df['Month'].dt.strftime('%b-%y').unique().tolist())
        month_options = ['All'] + sorted_months
        selected_month = st.selectbox("Select Month", month_options)
        if selected_month != 'All':
            filtered_df = filtered_df[filtered_df['Month'].dt.strftime('%b-%y') == selected_month]
    
    # Filter by Tier
    if 'Tier' in df.columns:
        tier_options = ['All'] + sorted(df['Tier'].dropna().unique().tolist())
        selected_tier = st.selectbox("Select Tier", tier_options)
        if selected_tier != 'All':
            filtered_df = filtered_df[filtered_df['Tier'] == selected_tier]
    
    # Filter by Platform
    if 'Platform' in df.columns:
        platform_options = ['All'] + sorted(df['Platform'].dropna().unique().tolist())
        selected_platform = st.selectbox("Select Platform", platform_options)
        if selected_platform != 'All':
            filtered_df = filtered_df[filtered_df['Platform'] == selected_platform]

# ============ FORMATTING FUNCTIONS ============
def format_number(num):
    if pd.isna(num) or num == 0:
        return "0"
    num = float(num)
    if num >= 1_000_000_000:
        val = num/1_000_000_000
        return f"{val:.1f}B".replace('.0B', 'B')
    elif num >= 1_000_000:
        val = num/1_000_000
        return f"{val:.1f}M".replace('.0M', 'M')
    elif num >= 1_000:
        val = num/1_000
        return f"{val:.1f}K".replace('.0K', 'K')
    else:
        return f"{num:,.0f}"

def format_currency(num):
    if pd.isna(num) or num == 0:
        return "Rp 0"
    num = float(num)
    if num >= 1_000_000_000:
        val = num/1_000_000_000
        return f"Rp {val:.1f}B".replace('.0B', 'B')
    elif num >= 1_000_000:
        val = num/1_000_000
        return f"Rp {val:.1f}M".replace('.0M', 'M')
    elif num >= 1_000:
        val = num/1_000
        return f"Rp {val:.1f}K".replace('.0K', 'K')
    else:
        return f"Rp {num:,.0f}"

def format_percent(num):
    if pd.isna(num):
        return "0%"
    if num <= 1:
        num = num * 100
    formatted = f"{num:.2f}%"
    formatted = formatted.replace('.00%', '%')
    if '.' in formatted:
        while formatted.endswith('0%'):
            formatted = formatted[:-2] + '%'
        if formatted.endswith('.%'):
            formatted = formatted[:-2] + '%'
    return formatted

def format_currency_short(num):
    if pd.isna(num) or num == 0:
        return "Rp 0"
    return f"Rp {num:,.2f}"

# ============ DONUT CHART FUNCTION (CENTERED HORIZONTAL LEGEND) ============
def create_donut_chart(data, name_col, value_col, colors=None):
    """Create a donut chart with percentage labels on segments and a clean vertical legend"""
    df = data.reset_index()
    df.columns = [name_col, value_col]
    
    total = df[value_col].sum()
    df['percentage'] = (df[value_col] / total * 100).round(1)
    
    if colors is None:
        colors = [DARK_BLUE, LIGHT_BLUE, '#6ba3d9', '#a8c8e8', '#d4e4f0']
    
    chart = alt.Chart(df).mark_arc(
        innerRadius=70,
        cornerRadius=5,
        stroke='white',
        strokeWidth=2
    ).encode(
        theta=alt.Theta(value_col + ':Q', stack=True),
        color=alt.Color(name_col + ':N', 
                        legend=alt.Legend(
                            title=None, 
                            orient='right', # VERTICAL LEGEND
                            labelFontSize=12,
                            labelLimit=200
                        ),
                        scale=alt.Scale(range=colors[:len(df)])),
        tooltip=[
            alt.Tooltip(name_col + ':N', title='Category'),
            alt.Tooltip(value_col + ':Q', format=',.0f', title='Spend'),
            alt.Tooltip('percentage:Q', format='.1f', title='%')
        ]
    ).properties(
        width=300, 
        height=300
    )
    
    text = alt.Chart(df).mark_text(
        fontSize=12,
        fontWeight='bold',
        color='white',
        stroke='white',
        strokeWidth=0.5
    ).encode(
        theta=alt.Theta(value_col + ':Q', stack=True),
        text=alt.Text('percentage:Q', format='.1f')
    )
    
    final_chart = (chart + text).properties(
        width=350,  # Slightly wider to accommodate the vertical legend on the right
        height=300
    ).configure_view(
        strokeWidth=0
    ).configure_legend(
        orient='right', # Keep it strictly vertical on the right
        labelFontSize=12,
        titleFontSize=14,
        labelLimit=150,
        labelPadding=10,
        rowPadding=5
    )
    
    return final_chart

# ============ BAR CHART FUNCTION (FORCED CHRONOLOGICAL ORDER) ============
def create_bar_chart(data, x_col, y_col, color=None):
    df = data.reset_index()
    df.columns = [x_col, y_col]
    
    bars = alt.Chart(df).mark_bar(
        color=color if color else DARK_BLUE,
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    ).encode(
        x=alt.X(x_col + ':O', 
                axis=alt.Axis(labels=True, title=None, labelAngle=-45),
                # FORCE to follow the exact order of the dataframe (Jan -> Jul)
                sort=None 
                ),
        y=alt.Y(y_col + ':Q', 
                axis=alt.Axis(labels=False, title=None, grid=False)),
        tooltip=[x_col, alt.Tooltip(y_col, format=',.0f')]
    )
    
    text = alt.Chart(df).mark_text(
        align='center',
        baseline='bottom',
        dy=-10,
        fontSize=11,
        fontWeight='bold',
        color=DARK_BLUE
    ).encode(
        # FORCE text to follow the exact same order
        x=alt.X(x_col + ':O', sort=None),
        y=alt.Y(y_col + ':Q'),
        text=alt.Text(y_col + ':Q', format=',.0f')
    )
    
    chart = (bars + text).properties(
        width='container',
        height=350
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        labelFontSize=12,
        labelColor='#666',
        grid=False
    )
    
    return chart

# ============ HEADER STYLE FUNCTIONS ============
def section_header_with_divider(title):
    st.divider()
    st.markdown(f"""
    <div style="color: #000000; font-size: 24px; font-weight: bold; margin-bottom: 15px; margin-top: 10px;">
        {title}
    </div>
    """, unsafe_allow_html=True)

def section_header_no_divider(title):
    st.markdown(f"""
    <div style="color: #000000; font-size: 24px; font-weight: bold; margin-bottom: 15px; margin-top: 10px;">
        {title}
    </div>
    """, unsafe_allow_html=True)

# ============ CALCULATE CPV ============
if 'Actual_Spends_IDR' in filtered_df.columns and 'Views' in filtered_df.columns:
    filtered_df['CPV_Calculated'] = filtered_df['Actual_Spends_IDR'] / filtered_df['Views']
    filtered_df['CPV_Calculated'] = filtered_df['CPV_Calculated'].replace([np.inf, -np.inf], np.nan)
    filtered_df['CPV_Calculated'] = filtered_df['CPV_Calculated'].fillna(0)

# ============ CALCULATE KPIS ============
total_views = filtered_df['Views'].sum() if 'Views' in filtered_df.columns else 0
total_engagement = (filtered_df['Likes'].sum() + filtered_df['Comments'].sum() + filtered_df['Share'].sum()) if all(col in filtered_df.columns for col in ['Likes', 'Comments', 'Share']) else 0
total_spend = filtered_df['Actual_Spends_IDR'].sum() if 'Actual_Spends_IDR' in filtered_df.columns else 0
total_reach = filtered_df['Reach'].sum() if 'Reach' in filtered_df.columns else 0

# ============ FIXED KOL COUNT ============
if 'KOL_Name' in filtered_df.columns:
    kol_cleaned = filtered_df['KOL_Name'].astype(str).str.strip()
    kol_cleaned = kol_cleaned.str.replace(r'\s+', ' ', regex=True)
    kol_cleaned = kol_cleaned.str.replace('\u200b', '', regex=False)
    kol_cleaned = kol_cleaned.str.replace('\u00a0', ' ', regex=False)
    kol_cleaned = kol_cleaned.str.title()
    total_kols = kol_cleaned.nunique()
else:
    total_kols = 0

total_posts = len(filtered_df)

# ============ FIXED ER CALCULATION (DIVIDED BY 100) ============
if 'ER' in filtered_df.columns:
    er_values = filtered_df['ER'].dropna()
    engagement_rate = (er_values.mean() / 100) if len(er_values) > 0 else 0
else:
    engagement_rate = 0

avg_cpv = filtered_df['CPV_Calculated'].mean() if 'CPV_Calculated' in filtered_df.columns else 0

# ============ KPI METRICS - ROW 1 ============
section_header_no_divider("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div style="text-align: center">
        <p style="margin-bottom: 0; color: #888; font-size: 14px;">Views</p>
        <p style="font-size: 24px; font-weight: bold; margin-top: 0;">{format_number(total_views)}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="text-align: center">
        <p style="margin-bottom: 0; color: #888; font-size: 14px;">Reach</p>
        <p style="font-size: 24px; font-weight: bold; margin-top: 0;">{format_number(total_reach)}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="text-align: center">
        <p style="margin-bottom: 0; color: #888; font-size: 14px;">Engagement</p>
        <p style="font-size: 24px; font-weight: bold; margin-top: 0;">{format_number(total_engagement)}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="text-align: center">
        <p style="margin-bottom: 0; color: #888; font-size: 14px;">Spend</p>
        <p style="font-size: 24px; font-weight: bold; margin-top: 0;">{format_currency(total_spend)}</p>
    </div>
    """, unsafe_allow_html=True)

# ============ KPI METRICS - ROW 2 ============
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div style="text-align: center">
        <p style="margin-bottom: 0; color: #888; font-size: 14px;">Total KOLs</p>
        <p style="font-size: 24px; font-weight: bold; margin-top: 0;">{total_kols:,}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="text-align: center">
        <p style="margin-bottom: 0; color: #888; font-size: 14px;">Total Posts</p>
        <p style="font-size: 24px; font-weight: bold; margin-top: 0;">{total_posts:,}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="text-align: center">
        <p style="margin-bottom: 0; color: #888; font-size: 14px;">ER</p>
        <p style="font-size: 24px; font-weight: bold; margin-top: 0;">{format_percent(engagement_rate)}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="text-align: center">
        <p style="margin-bottom: 0; color: #888; font-size: 14px;">Avg CPV</p>
        <p style="font-size: 24px; font-weight: bold; margin-top: 0;">{format_currency_short(avg_cpv)}</p>
    </div>
    """, unsafe_allow_html=True)

# ============ VISUALIZATIONS ============
section_header_with_divider("Visualizations")

# ============ SPEND BY MONTH (SORTED CHRONOLOGICALLY) ============
st.markdown(f"""
<div style="text-align: center; font-size: 18px; font-weight: bold; color: {DARK_BLUE}; margin-bottom: 10px;">
    Spend by Month
</div>
""", unsafe_allow_html=True)

# Ensure we aggregate with .sort_index() to maintain the pure chronological data
monthly_data = filtered_df.groupby('Month')['Actual_Spends_IDR'].sum().sort_index()

if not monthly_data.empty:
    # Convert to short names for display
    monthly_data.index = monthly_data.index.strftime('%b')
    chart = create_bar_chart(monthly_data, 'Month', 'Actual_Spends_IDR', DARK_BLUE)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No data available for Spend by Month")

# ============ DONUT CHARTS ============
st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(f"""
    <div style="text-align: center; font-size: 18px; font-weight: bold; color: {DARK_BLUE}; margin-bottom: 10px;">
        Spend by Platform
    </div>
    """, unsafe_allow_html=True)
    
    platform_data = filtered_df.groupby('Platform')['Actual_Spends_IDR'].sum().sort_values(ascending=False)
    platform_data = platform_data[platform_data > 0]
    
    if not platform_data.empty:
        chart = create_donut_chart(platform_data, 'Platform', 'Actual_Spends_IDR')
        st.altair_chart(chart, use_container_width=False)
    else:
        st.info("No data available for Spend by Platform")

with col2:
    st.markdown(f"""
    <div style="text-align: center; font-size: 18px; font-weight: bold; color: {DARK_BLUE}; margin-bottom: 10px;">
        Spend by Tier
    </div>
    """, unsafe_allow_html=True)
    
    tier_data = filtered_df.groupby('Tier')['Actual_Spends_IDR'].sum().sort_values(ascending=False)
    tier_data = tier_data[tier_data > 0]
    
    if not tier_data.empty:
        chart = create_donut_chart(tier_data, 'Tier', 'Actual_Spends_IDR', [LIGHT_BLUE, DARK_BLUE, '#6ba3d9', '#a8c8e8'])
        st.altair_chart(chart, use_container_width=False)
    else:
        st.info("No data available for Spend by Tier")

# ============ TOP PERFORMING KOLS ============
section_header_with_divider("Top 10 KOL Performance")

if 'KOL_Name' in filtered_df.columns:
    kol_agg = filtered_df.groupby('KOL_Name').agg({
        'Likes': 'sum',
        'Comments': 'sum',
        'Share': 'sum',
        'Followers_Number': 'max',
        'Actual_Spends_IDR': 'sum',
        'Tier': 'first'
    }).reset_index()
    
    kol_agg['ER_Per_Follower'] = (kol_agg['Likes'] + kol_agg['Comments'] + kol_agg['Share']) / kol_agg['Followers_Number']
    kol_agg['ER_Per_Follower'] = kol_agg['ER_Per_Follower'].replace([np.inf, -np.inf], np.nan)
    kol_agg['ER_Per_Follower'] = kol_agg['ER_Per_Follower'].fillna(0)
    
    kol_agg = kol_agg.sort_values('ER_Per_Follower', ascending=False)
    
    top_kols = kol_agg.head(10).copy()
    
    top_kols['Rank'] = ['#' + str(i+1) for i in range(len(top_kols))]
    
    top_kols['KOL'] = top_kols['KOL_Name']
    top_kols['ER'] = top_kols['ER_Per_Follower'].apply(format_percent)
    top_kols['Cost'] = top_kols['Actual_Spends_IDR'].apply(format_currency)
    
    display_df = top_kols[['Rank', 'KOL', 'Tier', 'ER', 'Cost']]
    
    st.markdown("""
    <style>
    .dataframe-container {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    .dataframe-container table {
        width: 80% !important;
        margin: 0 auto;
        border-collapse: collapse;
        font-family: inherit;
    }
    .dataframe-container thead tr th {
        text-align: center !important;
        background-color: #f0f4f8;
        color: #1a3a5c;
        font-weight: bold;
        padding: 10px 15px;
        border-bottom: 2px solid #1a3a5c;
    }
    .dataframe-container tbody tr td {
        text-align: left !important;
        padding: 8px 15px;
        border-bottom: 1px solid #e0e0e0;
    }
    .dataframe-container tbody tr td:first-child {
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    table_html = display_df.to_html(index=False, classes='dataframe-container')
    st.markdown(f'<div class="dataframe-container">{table_html}</div>', unsafe_allow_html=True)

# ============ DATA TABLE ============
section_header_with_divider("Full Data Table")

display_full_df = filtered_df.copy()

# ============ NEW: DROP THE UNNAMED COLUMNS ============
# This removes columns like "Unnamed: _10" and "Unnamed: _11" from the table
display_full_df = display_full_df.loc[:, ~display_full_df.columns.str.startswith('Unnamed')]

for col in ['Views', 'Reach', 'Likes', 'Comments', 'Share', 'Followers_Number', 'Actual_Spends_IDR']:
    if col in display_full_df.columns:
        display_full_df[col] = display_full_df[col].apply(format_number)

for col in ['ER', 'ER_Views', 'VR']:
    if col in display_full_df.columns:
        display_full_df[col] = display_full_df[col].apply(format_percent)

if 'CPV_Calculated' in display_full_df.columns:
    display_full_df['CPV_Calculated'] = display_full_df['CPV_Calculated'].apply(format_currency_short)

st.dataframe(display_full_df, use_container_width=True)
st.caption(f"Showing {len(filtered_df):,} rows out of {len(df):,} total")

# ============ DOWNLOAD BUTTON ============
if not filtered_df.empty:
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name='filtered_union_data_kol.csv',
        mime='text/csv'
    )

# ============ COLUMN INFO ============
with st.expander("Column Information"):
    col_info = pd.DataFrame({
        'Column': df.columns,
        'Type': df.dtypes.astype(str),
        'Unique Values': [df[col].nunique() for col in df.columns],
        'Missing Values': [df[col].isnull().sum() for col in df.columns]
    })
    st.dataframe(col_info)
