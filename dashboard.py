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

# ============ HELPER FUNCTION TO CLEAN KOL NAME ============
def clean_kol_name(name):
    """Remove numbers/prefixes before KOL name and clean up"""
    if pd.isna(name):
        return name
    name = str(name).strip()
    # Remove patterns like "593 " or "123 " at the start
    name = re.sub(r'^\d+\s+', '', name)
    # Remove any remaining leading numbers
    name = re.sub(r'^\d+', '', name)
    name = name.strip()
    # Remove zero-width spaces and other special chars
    name = name.replace('\u200b', '').replace('\u00a0', ' ')
    # Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name)
    return name

# ============ APPLY CLEAN KOL NAME TO DATAFRAME ============
if 'KOL_Name' in df.columns:
    df['KOL_Name_Original'] = df['KOL_Name']
    df['KOL_Name'] = df['KOL_Name'].apply(clean_kol_name)

# ============ SIDEBAR FILTERS (WITH MULTISELECT) ============
with st.sidebar:
    st.subheader("Filters")
    
    filtered_df = df.copy()
    
    # Filter by Month - MULTISELECT with "Select All" option
    if 'Month' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Month']):
        # Get unique months and sort them chronologically by the datetime values
        unique_months = df['Month'].unique()
        # Sort the datetime values
        sorted_months_dt = sorted(unique_months)
        # Convert to string format for display
        sorted_months = [dt.strftime('%b-%y') for dt in sorted_months_dt]
        
        # Add "Select All" option
        month_options = ['Select All'] + sorted_months
        selected_months = st.multiselect(
            "Select Months",
            options=month_options,
            default=['Select All']
        )
        
        # Handle "Select All" selection
        if 'Select All' in selected_months:
            selected_months = sorted_months
        
        if selected_months:
            filtered_df = filtered_df[filtered_df['Month'].dt.strftime('%b-%y').isin(selected_months)]
    
    # Filter by Tier - MULTISELECT with "Select All" option
    if 'Tier' in df.columns:
        tier_options = ['Select All'] + sorted(df['Tier'].dropna().unique().tolist())
        selected_tiers = st.multiselect(
            "Select Tiers",
            options=tier_options,
            default=['Select All']
        )
        
        # Handle "Select All" selection
        if 'Select All' in selected_tiers:
            selected_tiers = sorted(df['Tier'].dropna().unique().tolist())
        
        if selected_tiers:
            filtered_df = filtered_df[filtered_df['Tier'].isin(selected_tiers)]
    
    # Filter by Platform - MULTISELECT with "Select All" option
    if 'Platform' in df.columns:
        platform_options = ['Select All'] + sorted(df['Platform'].dropna().unique().tolist())
        selected_platforms = st.multiselect(
            "Select Platforms",
            options=platform_options,
            default=['Select All']
        )
        
        # Handle "Select All" selection
        if 'Select All' in selected_platforms:
            selected_platforms = sorted(df['Platform'].dropna().unique().tolist())
        
        if selected_platforms:
            filtered_df = filtered_df[filtered_df['Platform'].isin(selected_platforms)]
    
    # Add a "Clear All Filters" button
    if st.button("🔄 Clear All Filters", use_container_width=True):
        st.rerun()

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

# ============ DONUT CHART FUNCTION ============
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
                            orient='right',
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
        width=350,
        height=300
    ).configure_view(
        strokeWidth=0
    ).configure_legend(
        orient='right',
        labelFontSize=12,
        titleFontSize=14,
        labelLimit=150,
        labelPadding=10,
        rowPadding=5
    )
    
    return final_chart

# ============ BAR CHART FUNCTION ============
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

monthly_data = filtered_df.groupby('Month')['Actual_Spends_IDR'].sum().sort_index()

if not monthly_data.empty:
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

# ============ KOL SEARCH FEATURE ============
section_header_with_divider("🔍 Search KOL Performance")

st.markdown("""
<div style="margin-bottom: 15px; color: #555; font-size: 14px;">
    Enter a KOL name to view their detailed performance metrics across all campaigns.
</div>
""", unsafe_allow_html=True)

# Helper function to format ER (divide by 100)
def format_er_display(value):
    """Format ER by dividing by 100 if needed"""
    if pd.isna(value):
        return "0%"
    if value > 1:
        return format_percent(value / 100)
    else:
        return format_percent(value)

# Create search input
search_col1, search_col2 = st.columns([2, 1])

with search_col1:
    kol_search = st.text_input(
        "Enter KOL Name",
        placeholder="e.g., bschristy, _ninitata_, A'yun, or any KOL name",
        key="kol_search_input"
    )

with search_col2:
    st.write("")  # Spacer
    st.write("")  # Spacer
    search_button = st.button("🔍 Search", use_container_width=True)

# Only show results if there's a search query
if kol_search or search_button:
    if kol_search.strip():
        # Clean the search term
        search_term = kol_search.strip().lower()
        search_term = re.sub(r'^\d+\s+', '', search_term)  # Remove numbers from search term
        
        # Search in the filtered data
        if 'KOL_Name' in filtered_df.columns:
            # Create a copy of filtered data for searching
            search_df = filtered_df.copy()
            
            # KOL names are already cleaned in the main dataframe
            search_df['KOL_Name_Search'] = search_df['KOL_Name'].str.lower()
            
            # Find matching KOLs (partial match on cleaned name)
            matching_kols = search_df[search_df['KOL_Name_Search'].str.contains(search_term, na=False, case=False)]
            
            if not matching_kols.empty:
                # Get unique KOLs that match
                unique_kols = matching_kols['KOL_Name'].unique()
                
                st.success(f"✅ Found {len(unique_kols)} KOL(s) matching '{kol_search}'")
                
                # Display results for each matching KOL
                for kol_name in unique_kols:
                    kol_data = matching_kols[matching_kols['KOL_Name'] == kol_name].copy()
                    
                    # Create an expander for each KOL
                    with st.expander(f"📊 {kol_name}", expanded=True):
                        # Prepare display data
                        display_kol = kol_data.copy()
                        
                        # Format columns for display
                        for col in ['Views', 'Reach', 'Likes', 'Comments', 'Share', 'Followers_Number', 'Actual_Spends_IDR']:
                            if col in display_kol.columns:
                                display_kol[col] = display_kol[col].apply(format_number)
                        
                        # Format ER by dividing by 100
                        for col in ['ER', 'ER_Views', 'VR']:
                            if col in display_kol.columns:
                                if display_kol[col].dtype == 'object':
                                    display_kol[col] = pd.to_numeric(display_kol[col].astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')
                                display_kol[col] = display_kol[col].apply(format_er_display)
                        
                        # Calculate CPV
                        if 'CPV_Calculated' in display_kol.columns:
                            display_kol['CPV'] = display_kol['CPV_Calculated'].apply(format_currency_short)
                        elif 'CPV_Rp' in display_kol.columns:
                            display_kol['CPV'] = display_kol['CPV_Rp'].apply(format_currency_short)
                        
                        # Select columns for display
                        display_columns = []
                        
                        # Define desired column order based on example
                        desired_order = ['KOL_Name', 'Category', 'Brands', 'Tier', 'Objective', 'Platform', 'Month', 'Actual_Spends_IDR', 'Views', 'ER', 'VR', 'Likes', 'CPV']
                        
                        for col in desired_order:
                            if col in display_kol.columns:
                                if col == 'CPV_Rp':
                                    continue
                                if col == 'CPV_Calculated':
                                    display_columns.append('CPV')
                                else:
                                    display_columns.append(col)
                        
                        extra_columns = ['Reach', 'Comments', 'Share', 'Followers_Number', 'ER_Views', 'Engagement']
                        for col in extra_columns:
                            if col in display_kol.columns and col not in display_columns:
                                display_columns.append(col)
                        
                        display_columns = list(dict.fromkeys(display_columns))
                        
                        if not display_columns:
                            display_columns = ['KOL_Name', 'Platform', 'Month', 'Actual_Spends_IDR', 'Views']
                        
                        display_df = display_kol[display_columns].copy()
                        
                        column_rename = {
                            'KOL_Name': 'KOL Name',
                            'Actual_Spends_IDR': 'Cost',
                            'Followers_Number': 'Followers',
                            'ER_Views': 'ER Views',
                            'Engagement': 'Engagement'
                        }
                        
                        for old, new in column_rename.items():
                            if old in display_df.columns:
                                display_df = display_df.rename(columns={old: new})
                        
                        if 'Month' in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df['Month']):
                            display_df['Month'] = display_df['Month'].dt.strftime('%b-%y')
                        
                        # Display the table - HIDE THE INDEX
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                        
                        st.markdown("---")
                        st.markdown("**📈 Performance Summary**")
                        
                        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
                        
                        with summary_col1:
                            total_posts_kol = len(kol_data)
                            st.metric("Total Posts", total_posts_kol)
                        
                        with summary_col2:
                            total_views_kol = kol_data['Views'].sum() if 'Views' in kol_data.columns else 0
                            st.metric("Total Views", format_number(total_views_kol))
                        
                        with summary_col3:
                            total_spend_kol = kol_data['Actual_Spends_IDR'].sum() if 'Actual_Spends_IDR' in kol_data.columns else 0
                            st.metric("Total Spend", format_currency(total_spend_kol))
                        
                        with summary_col4:
                            if 'ER' in kol_data.columns:
                                er_values = kol_data['ER'].dropna()
                                if len(er_values) > 0:
                                    avg_er = er_values.mean() / 100
                                    st.metric("Avg ER", format_percent(avg_er))
                                else:
                                    st.metric("Avg ER", "N/A")
                            else:
                                st.metric("Avg ER", "N/A")
                
            else:
                st.warning(f"❌ No KOL found matching '{kol_search}'. Please try a different name.")
                
                if 'KOL_Name' in filtered_df.columns:
                    all_kols = filtered_df['KOL_Name'].unique()[:10]
                    all_kols = [k for k in all_kols if k and not pd.isna(k)]
                    if len(all_kols) > 0:
                        st.markdown("**💡 Suggestions:**")
                        st.write(", ".join(all_kols[:5]))
                        if len(all_kols) > 5:
                            st.write(f"... and {len(all_kols) - 5} more")
        else:
            st.warning("KOL_Name column not found in the data.")
    else:
        st.info("Please enter a KOL name to search.")
else:
    st.info("👆 Enter a KOL name above and click Search to view their performance details.")

if kol_search:
    if st.button("🔄 Clear Search"):
        st.rerun()

# ============ DATA TABLE ============
section_header_with_divider("Full Data Table")

display_full_df = filtered_df.copy()

display_full_df = display_full_df.loc[:, ~display_full_df.columns.str.startswith('Unnamed')]

for col in ['Views', 'Reach', 'Likes', 'Comments', 'Share', 'Followers_Number', 'Actual_Spends_IDR']:
    if col in display_full_df.columns:
        display_full_df[col] = display_full_df[col].apply(format_number)

for col in ['ER', 'ER_Views', 'VR']:
    if col in display_full_df.columns:
        display_full_df[col] = display_full_df[col].apply(format_percent)

if 'CPV_Calculated' in display_full_df.columns:
    display_full_df['CPV_Calculated'] = display_full_df['CPV_Calculated'].apply(format_currency_short)

st.dataframe(display_full_df, use_container_width=True, hide_index=True)
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
