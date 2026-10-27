"""Streamlit Interactive Weather Analytics Dashboard.

Provides interactive visualizations and analysis powered by MongoDB aggregation pipelines.
Pages:
  A. Overview: KPI metrics, database coverage, and key meteorological insights.
  B. Temperature Trends: Hourly, daily, and monthly analysis with min/max envelopes.
  C. City Comparison: Multi-city comparison across temperature, rainfall, humidity, and wind.
  D. Rainfall Analysis: Monthly precipitation totals, rain hours, and wettest recorded dates.
  E. Wind & Extreme Weather: High-wind observations, extreme temperatures, and distributions.
  F. Weather Relationships: Bounded scatter plots and correlation matrix.
  G. Data Explorer: Paginated records viewer with server-side filters and CSV export.
  H. Database & Ingestion: Local MongoDB diagnostics, ingestion history, and interactive fetcher.
"""

import os
from datetime import datetime, date, timedelta
from typing import List, Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

import config
import db
import analytics
import weather_fetcher
import import_data

# Set Streamlit page configuration
st.set_page_config(
    page_title="Weather Analytics | Local MongoDB",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling, KPI cards, and responsive layout
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .kpi-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 18px 20px;
        color: #f8fafc;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        margin-bottom: 12px;
    }
    .kpi-title {
        font-size: 0.82rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #38bdf8;
        line-height: 1.2;
    }
    .kpi-subtitle {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 4px;
    }
    .status-badge-ok {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .status-badge-err {
        background-color: #7f1d1d;
        color: #f87171;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .attribution-box {
        background: rgba(30, 41, 59, 0.5);
        border-left: 4px solid #38bdf8;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def check_db_health():
    """Verify local MongoDB connection and return server info or error."""
    try:
        client = db.get_mongodb_client()
        info = db.ping_server(client)
        return True, info, None
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        return False, None, str(exc)
    except Exception as exc:
        return False, None, str(exc)


# Sidebar navigation and global status
st.sidebar.title("🌤️ Weather Analytics")
st.sidebar.caption("Big Data Processing with Local MongoDB")

is_connected, server_info, conn_error = check_db_health()

if is_connected:
    st.sidebar.markdown(
        f'<span class="status-badge-ok">● MongoDB Server Active (v{server_info.get("version")})</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption(f"Host: `{server_info.get('address', ['127.0.0.1', 27017])[0]}` | DB: `{config.MONGODB_DATABASE}`")
else:
    st.sidebar.markdown(
        '<span class="status-badge-err">● MongoDB Server Offline</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.warning(
        "Local MongoDB Community Server is not running on 127.0.0.1:27017.\n"
        "Please run `Start-Service MongoDB` in PowerShell."
    )

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Temperature Trends",
        "City Comparison",
        "Rainfall Analysis",
        "Wind & Extreme Weather",
        "Weather Relationships",
        "Data Explorer",
        "Database & Ingestion",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Architecture Distinction:**
    - **Community Server**: Local NoSQL Database Engine.
    - **MongoDB Compass**: GUI Query Viewer.
    """
)


# -----------------------------------------------------------------------------
# PAGE A: OVERVIEW
# -----------------------------------------------------------------------------
if page == "Overview":
    st.title("📊 Weather Analytics Overview")
    st.markdown("High-level summary of historical meteorological observations stored in local MongoDB.")

    if not is_connected:
        st.error(f"Cannot connect to local MongoDB Community Server at `{config.MONGODB_URI}`.")
        st.info("Check that MongoDB Community Server is installed and started as a Windows service (`Start-Service MongoDB`).")
        st.stop()

    summary = analytics.get_database_summary()
    total_obs = summary.get("total_observations", 0)

    if total_obs == 0:
        st.warning(
            "⚠️ The local MongoDB database `weather_analytics` is currently empty.\n"
            "Navigate to the **Database & Ingestion** tab in the sidebar or run `python weather_fetcher.py` to ingest historical data."
        )
    else:
        # KPI Row
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        with kpi_col1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">Total Observations</div>
                    <div class="kpi-value">{total_obs:,}</div>
                    <div class="kpi-subtitle">{summary.get('city_count', 0)} Indian Cities Registered</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with kpi_col2:
            avg_temp = summary.get("avg_temperature_c")
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">Mean Temperature</div>
                    <div class="kpi-value">{avg_temp if avg_temp is not None else '--'} °C</div>
                    <div class="kpi-subtitle">Min: {summary.get('min_temperature_c', '--')} °C | Max: {summary.get('max_temperature_c', '--')} °C</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with kpi_col3:
            total_rain = summary.get("total_precipitation_mm", 0.0)
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">Total Cumulative Rain</div>
                    <div class="kpi-value">{total_rain:,.1f} mm</div>
                    <div class="kpi-subtitle">Across all monitored locations</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with kpi_col4:
            earliest = summary.get("earliest_date")
            latest = summary.get("latest_date")
            earliest_str = earliest.strftime("%b %Y") if earliest else "N/A"
            latest_str = latest.strftime("%b %Y") if latest else "N/A"
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">Temporal Coverage</div>
                    <div class="kpi-value" style="font-size: 1.35rem;">{earliest_str} – {latest_str}</div>
                    <div class="kpi-subtitle">Granularity: Hourly Reanalysis</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 🌆 Monitored Cities & Temperature Summary")
        df_cities = analytics.get_city_temperature_summary()
        if not df_cities.empty:
            col_chart, col_table = st.columns([3, 2])
            with col_chart:
                fig = px.bar(
                    df_cities,
                    x="city",
                    y="avg_temp_c",
                    color="avg_temp_c",
                    color_continuous_scale="Turbo",
                    title="Average Temperature by City (°C)",
                    labels={"avg_temp_c": "Avg Temp (°C)", "city": "City"},
                )
                fig.update_layout(height=380, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
            with col_table:
                st.write("**City Climate Metrics**")
                st.dataframe(
                    df_cities.rename(
                        columns={
                            "city": "City",
                            "avg_temp_c": "Avg (°C)",
                            "min_temp_c": "Min (°C)",
                            "max_temp_c": "Max (°C)",
                            "temp_range_c": "Range (°C)",
                            "observations": "Records",
                        }
                    ),
                    use_container_width=True,
                    height=340,
                )

        st.markdown("### 💡 Key Meteorological Insights")
        inc_c1, inc_c2 = st.columns(2)
        with inc_c1:
            st.info(
                f"**Hottest vs Coldest Cities:** Based on MongoDB aggregation, "
                f"**{df_cities.iloc[0]['city']}** records the highest average temperature ({df_cities.iloc[0]['avg_temp_c']} °C), "
                f"while **{df_cities.iloc[-1]['city']}** records the coolest average ({df_cities.iloc[-1]['avg_temp_c']} °C)."
            )
        with inc_c2:
            st.info(
                f"**High Diurnal Variation:** Cities with wide temperature spreads "
                f"(e.g., Delhi and Jaipur) experience seasonal continental extremes, whereas coastal cities "
                f"(Mumbai, Chennai, Kochi) exhibit narrower temperature ranges buffered by maritime humidity."
            )

    st.markdown(
        f'<div class="attribution-box">ℹ️ {weather_fetcher.SOURCE_ATTRIBUTION}</div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# PAGE B: TEMPERATURE TRENDS
# -----------------------------------------------------------------------------
elif page == "Temperature Trends":
    st.title("📈 Temperature Trends & Trajectories")
    st.markdown("Analyze diurnal and seasonal temperature patterns computed via MongoDB aggregation.")

    if not is_connected:
        st.error("MongoDB is offline.")
        st.stop()

    summary = analytics.get_database_summary()
    available_cities = summary.get("cities", list(config.CITY_REGISTRY.keys()))

    if not available_cities:
        st.warning("No data in database. Ingest weather observations first.")
        st.stop()

    # Filter controls
    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        sel_city = st.selectbox("Select City", ["All Cities"] + available_cities, index=1 if available_cities else 0)
    with f_col2:
        earliest_d = summary.get("earliest_date", datetime(2021, 1, 1)).date() if summary.get("earliest_date") else date(2021, 1, 1)
        latest_d = summary.get("latest_date", datetime(2025, 12, 31)).date() if summary.get("latest_date") else date(2025, 12, 31)
        date_range = st.date_input("Date Filter", [earliest_d, latest_d])
    with f_col3:
        aggregation_level = st.radio("Aggregation Level", ["Monthly Trends", "Daily Fluctuations"], horizontal=True)

    s_date = date_range[0] if len(date_range) > 0 else earliest_d
    e_date = date_range[1] if len(date_range) > 1 else latest_d

    target_cities = None if sel_city == "All Cities" else [sel_city]

    if aggregation_level == "Monthly Trends":
        df_monthly = analytics.get_monthly_temperature_trends(cities=target_cities, start_date=s_date, end_date=e_date)
        if df_monthly.empty:
            st.info("No matching records found for selected filters.")
        else:
            fig = px.line(
                df_monthly,
                x="year_month",
                y="avg_temp_c",
                color="city",
                title=f"Monthly Average Temperature (°C) - {sel_city}",
                markers=True,
                labels={"year_month": "Month", "avg_temp_c": "Avg Temp (°C)", "city": "City"},
            )
            fig.update_layout(height=480, template="plotly_dark", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            # Min-Max Temperature Envelopes
            if sel_city != "All Cities":
                st.markdown(f"#### Temperature Range Envelope for {sel_city}")
                fig_env = go.Figure()
                fig_env.add_trace(go.Scatter(
                    x=df_monthly["year_month"], y=df_monthly["max_temp_c"],
                    mode="lines", name="Maximum (°C)", line=dict(color="#f87171", width=2)
                ))
                fig_env.add_trace(go.Scatter(
                    x=df_monthly["year_month"], y=df_monthly["avg_temp_c"],
                    mode="lines+markers", name="Average (°C)", line=dict(color="#38bdf8", width=3)
                ))
                fig_env.add_trace(go.Scatter(
                    x=df_monthly["year_month"], y=df_monthly["min_temp_c"],
                    mode="lines", name="Minimum (°C)", line=dict(color="#34d399", width=2),
                    fill="tonexty", fillcolor="rgba(56, 189, 248, 0.15)"
                ))
                fig_env.update_layout(height=400, template="plotly_dark", title=f"Min / Avg / Max Thermal Envelope ({sel_city})")
                st.plotly_chart(fig_env, use_container_width=True)

    else:
        # Daily
        df_daily = analytics.get_daily_temperature_stats(cities=target_cities, start_date=s_date, end_date=e_date)
        if df_daily.empty:
            st.info("No daily records match the selected date filter.")
        else:
            fig = px.line(
                df_daily,
                x="date",
                y="avg_temp_c",
                color="city",
                title=f"Daily Mean Temperature (°C) - {sel_city}",
                labels={"date": "Date", "avg_temp_c": "Mean Temp (°C)", "city": "City"},
            )
            fig.update_layout(height=480, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)


# -----------------------------------------------------------------------------
# PAGE C: CITY COMPARISON
# -----------------------------------------------------------------------------
elif page == "City Comparison":
    st.title("🏙️ Multi-City Meteorological Comparison")
    st.markdown("Compare temperature, precipitation, humidity, and wind characteristics across Indian cities.")

    if not is_connected:
        st.error("MongoDB is offline.")
        st.stop()

    summary = analytics.get_database_summary()
    available_cities = summary.get("cities", list(config.CITY_REGISTRY.keys()))

    if not available_cities:
        st.warning("Database contains no observation records yet.")
        st.stop()

    selected_cities = st.multiselect(
        "Select Cities to Compare",
        available_cities,
        default=available_cities[:min(5, len(available_cities))],
    )

    if not selected_cities:
        st.info("Please select at least one city.")
        st.stop()

    metric_choice = st.selectbox(
        "Comparison Dimension",
        ["Temperature Profile", "Precipitation & Rainfall", "Relative Humidity", "Wind Speed"],
    )

    if metric_choice == "Temperature Profile":
        df_temp = analytics.get_city_temperature_summary(cities=selected_cities)
        col1, col2 = st.columns([3, 2])
        with col1:
            fig = go.Figure(data=[
                go.Bar(name="Min Temp (°C)", x=df_temp["city"], y=df_temp["min_temp_c"], marker_color="#60a5fa"),
                go.Bar(name="Avg Temp (°C)", x=df_temp["city"], y=df_temp["avg_temp_c"], marker_color="#f59e0b"),
                go.Bar(name="Max Temp (°C)", x=df_temp["city"], y=df_temp["max_temp_c"], marker_color="#ef4444"),
            ])
            fig.update_layout(barmode="group", height=420, template="plotly_dark", title="Thermal Extremes & Averages by City")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.write("**Thermal Metrics Comparison**")
            st.dataframe(df_temp, use_container_width=True)

    elif metric_choice == "Precipitation & Rainfall":
        df_rain = analytics.get_city_precipitation_totals(cities=selected_cities)
        fig = px.bar(
            df_rain,
            x="city",
            y="total_rainfall_mm",
            color="rainy_fraction_pct",
            color_continuous_scale="Teal",
            title="Total Cumulative Precipitation (mm) & % Rainy Hours",
            labels={"total_rainfall_mm": "Cumulative Rain (mm)", "rainy_fraction_pct": "% Rainy Hours"},
        )
        fig.update_layout(height=420, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_rain, use_container_width=True)

    elif metric_choice == "Relative Humidity":
        df_hum = analytics.get_humidity_summary(cities=selected_cities)
        fig = px.bar(
            df_hum,
            x="city",
            y="avg_humidity_pct",
            color="avg_humidity_pct",
            color_continuous_scale="Blues",
            title="Average Relative Humidity (%)",
            labels={"avg_humidity_pct": "Avg Humidity (%)"},
        )
        fig.update_layout(height=420, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_hum, use_container_width=True)

    elif metric_choice == "Wind Speed":
        df_wind = analytics.get_high_wind_observations(cities=selected_cities, threshold_kmh=15.0, limit=200)
        if not df_wind.empty:
            fig = px.box(
                df_wind,
                x="city",
                y="wind_speed_kmh",
                color="city",
                title="Wind Speed Distribution for Sustained Winds (>= 15 km/h)",
                labels={"wind_speed_kmh": "Wind Speed (km/h)"},
            )
            fig.update_layout(height=420, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recorded observations with sustained wind speed >= 15 km/h.")


# -----------------------------------------------------------------------------
# PAGE D: RAINFALL ANALYSIS
# -----------------------------------------------------------------------------
elif page == "Rainfall Analysis":
    st.title("🌧️ Precipitation & Monsoon Analytics")
    st.markdown("Investigate seasonal rainfall patterns, monsoon precipitation surges, and peak rainfall events.")

    if not is_connected:
        st.error("MongoDB is offline.")
        st.stop()

    summary = analytics.get_database_summary()
    available_cities = summary.get("cities", list(config.CITY_REGISTRY.keys()))

    if not available_cities:
        st.warning("No records present in local database.")
        st.stop()

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        sel_city = st.selectbox("Filter City", ["All Cities"] + available_cities)
    with r_col2:
        df_rain_totals = analytics.get_city_precipitation_totals()
        if not df_rain_totals.empty:
            wettest_city = df_rain_totals.iloc[0]["city"]
            wettest_val = df_rain_totals.iloc[0]["total_rainfall_mm"]
            st.success(f"🏆 Highest Total Precipitation: **{wettest_city}** with **{wettest_val:,.1f} mm**")

    target_cities = None if sel_city == "All Cities" else [sel_city]

    # Monthly rainfall trends
    df_monthly_rain = analytics.get_monthly_rainfall_trends(cities=target_cities)
    if not df_monthly_rain.empty:
        fig = px.bar(
            df_monthly_rain,
            x="year_month",
            y="total_rainfall_mm",
            color="city",
            title="Monthly Rainfall Trajectory (mm)",
            barmode="stack",
            labels={"year_month": "Year-Month", "total_rainfall_mm": "Rainfall (mm)"},
        )
        fig.update_layout(height=420, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    # Wettest recorded dates table
    st.markdown("### 🌊 Top Wettest Dates (Peak Single-Day Downpours)")
    df_wettest = analytics.get_wettest_dates(cities=target_cities, limit=15)
    if not df_wettest.empty:
        st.dataframe(
            df_wettest.rename(
                columns={
                    "city": "City",
                    "date": "Date",
                    "total_daily_rainfall_mm": "Daily Total (mm)",
                    "peak_hourly_rainfall_mm": "Peak Hourly Rate (mm/h)",
                }
            ),
            use_container_width=True,
        )
    else:
        st.info("No recorded rainfall events (> 0 mm) found.")


# -----------------------------------------------------------------------------
# PAGE E: WIND AND EXTREME WEATHER
# -----------------------------------------------------------------------------
elif page == "Wind & Extreme Weather":
    st.title("🌪️ Wind Speeds & Extreme Meteorological Records")
    st.markdown("Identify high-wind events and historical temperature extremes stored in local MongoDB.")

    if not is_connected:
        st.error("MongoDB is offline.")
        st.stop()

    st.markdown(
        """
        > **Data Notice:** Meteorological thresholds identified below represent statistical outlier queries
        > from historical reanalysis records. They do not constitute official real-time meteorological warnings.
        """
    )

    tab_temp_extreme, tab_wind = st.tabs(["🔥 Extreme Temperature Records", "💨 High Wind Events"])

    with tab_temp_extreme:
        high_df, low_df = analytics.get_extreme_temperatures(top_n=10)
        c_hot, c_cold = st.columns(2)
        with c_hot:
            st.markdown("#### 🔥 Top 10 Highest Recorded Temperatures")
            if not high_df.empty:
                st.dataframe(high_df, use_container_width=True)
            else:
                st.info("No data available.")
        with c_cold:
            st.markdown("#### ❄️ Top 10 Lowest Recorded Temperatures")
            if not low_df.empty:
                st.dataframe(low_df, use_container_width=True)
            else:
                st.info("No data available.")

    with tab_wind:
        wind_thresh = st.slider("Wind Speed Threshold (km/h)", min_value=15.0, max_value=80.0, value=30.0, step=5.0)
        df_wind_events = analytics.get_high_wind_observations(threshold_kmh=wind_thresh, limit=50)

        if not df_wind_events.empty:
            st.markdown(f"Found **{len(df_wind_events)}** observation(s) with wind speeds >= {wind_thresh} km/h:")
            fig = px.scatter(
                df_wind_events,
                x="timestamp",
                y="wind_speed_kmh",
                color="city",
                size="wind_speed_kmh",
                hover_data=["wind_direction_deg", "temperature_c"],
                title=f"High Wind Events (>= {wind_thresh} km/h)",
                labels={"timestamp": "Timestamp", "wind_speed_kmh": "Wind Speed (km/h)"},
            )
            fig.update_layout(height=420, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_wind_events, use_container_width=True)
        else:
            st.info(f"No records found exceeding {wind_thresh} km/h threshold.")


# -----------------------------------------------------------------------------
# PAGE F: WEATHER RELATIONSHIPS
# -----------------------------------------------------------------------------
elif page == "Weather Relationships":
    st.title("🔬 Meteorological Variable Relationships & Correlations")
    st.markdown("Explore multivariate interactions between temperature, humidity, precipitation, and atmospheric pressure.")

    st.warning("⚠️ **Statistical Note:** Correlation demonstrates empirical association, not causation.")

    if not is_connected:
        st.error("MongoDB is offline.")
        st.stop()

    # Bounded representative sample retrieval from MongoDB
    df_sample = analytics.get_relationship_sample(sample_size=3000)

    if df_sample.empty:
        st.info("Insufficient observation records in MongoDB to evaluate relationships.")
        st.stop()

    st.caption(f"Displaying a representative bounded sample of {len(df_sample):,} observations for responsive visualization.")

    col_x, col_y, col_color = st.columns(3)
    options = {
        "temperature_c": "Temperature (°C)",
        "relative_humidity_pct": "Relative Humidity (%)",
        "precipitation_mm": "Precipitation (mm)",
        "wind_speed_kmh": "Wind Speed (km/h)",
        "pressure_msl_hpa": "Atmospheric Pressure (hPa)",
    }
    with col_x:
        x_axis = st.selectbox("X Axis Variable", list(options.keys()), index=0, format_func=lambda k: options[k])
    with col_y:
        y_axis = st.selectbox("Y Axis Variable", list(options.keys()), index=1, format_func=lambda k: options[k])
    with col_color:
        color_var = st.selectbox("Color By", ["city", "temperature_c", "relative_humidity_pct"], index=0)

    fig_scatter = px.scatter(
        df_sample,
        x=x_axis,
        y=y_axis,
        color=color_var,
        opacity=0.6,
        trendline="ols",
        title=f"Scatter: {options[x_axis]} vs {options[y_axis]}",
        labels={x_axis: options[x_axis], y_axis: options[y_axis]},
    )
    fig_scatter.update_layout(height=480, template="plotly_dark")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Correlation Matrix
    st.markdown("### 📊 Pearson Correlation Matrix")
    corr_cols = [c for c in options.keys() if c in df_sample.columns]
    corr_df = df_sample[corr_cols].dropna().corr()

    fig_corr = px.imshow(
        corr_df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1.0,
        zmax=1.0,
        labels=dict(x="Variable", y="Variable", color="Correlation"),
    )
    fig_corr.update_layout(height=400, template="plotly_dark")
    st.plotly_chart(fig_corr, use_container_width=True)


# -----------------------------------------------------------------------------
# PAGE G: DATA EXPLORER
# -----------------------------------------------------------------------------
elif page == "Data Explorer":
    st.title("🔍 Weather Data Explorer & Export")
    st.markdown("Server-side paginated queries against local MongoDB with custom filters and CSV export.")

    if not is_connected:
        st.error("MongoDB is offline.")
        st.stop()

    summary = analytics.get_database_summary()
    available_cities = summary.get("cities", list(config.CITY_REGISTRY.keys()))

    # Filter bar
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        f_city = st.selectbox("Filter City", ["All Cities"] + available_cities)
    with f2:
        f_gran = st.selectbox("Granularity", ["All", "hourly", "daily"])
    with f3:
        f_source = st.selectbox("Source", ["All"] + summary.get("sources", ["open_meteo", "csv_import"]))
    with f4:
        page_size = st.selectbox("Records Per Page", [25, 50, 100, 250], index=1)

    # Date range filters
    d1, d2 = st.columns(2)
    with d1:
        start_d = st.date_input("Start Date", value=None)
    with d2:
        end_d = st.date_input("End Date", value=None)

    page_num = st.number_input("Page Number", min_value=1, value=1, step=1)

    df_page, total_count = analytics.get_explorer_records(
        city=f_city,
        granularity=f_gran,
        source=f_source,
        start_date=start_d,
        end_date=end_d,
        page=page_num,
        page_size=page_size,
    )

    st.write(f"**Showing Page {page_num}** ({len(df_page)} records) of **{total_count:,} total matching records** in MongoDB.")

    if not df_page.empty:
        st.dataframe(df_page, use_container_width=True, height=450)

        # Export current view or filtered set
        csv_data = df_page.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Current Page as CSV",
            data=csv_data,
            file_name=f"weather_export_page_{page_num}.csv",
            mime="text/csv",
        )
    else:
        st.info("No documents match the specified query filters.")


# -----------------------------------------------------------------------------
# PAGE H: DATABASE & INGESTION
# -----------------------------------------------------------------------------
elif page == "Database & Ingestion":
    st.title("⚙️ Local MongoDB Diagnostics & Data Ingestion")
    st.markdown("Monitor database status, inspect data quality completeness, and initiate data imports.")

    # Status Section
    st.markdown("### 🔌 Server Connectivity")
    if is_connected:
        st.success(
            f"✅ **Connected to MongoDB Community Server:** Version {server_info.get('version')} "
            f"on `{server_info.get('address')}`"
        )
    else:
        st.error(
            f"❌ **Disconnected:** Unable to reach MongoDB Community Server.\n\n"
            f"**Error Details:** `{conn_error}`\n\n"
            f"**Action Required:** Open PowerShell and execute:\n"
            f"```powershell\nGet-Service MongoDB\nStart-Service MongoDB\n```"
        )

    if is_connected:
        tab_status, tab_quality, tab_api_fetch, tab_csv_import = st.tabs(
            ["📊 Collection Status", "🧪 Data Quality Report", "🌐 Fetch Open-Meteo API", "📁 Import CSV File"]
        )

        with tab_status:
            col_obs = db.get_collection(config.COLLECTION_WEATHER_OBSERVATIONS)
            col_runs = db.get_collection(config.COLLECTION_INGESTION_RUNS)

            obs_count = col_obs.count_documents({})
            runs_count = col_runs.count_documents({})

            st.write(f"**Collection `weather_observations`:** `{obs_count:,}` documents")
            st.write(f"**Collection `ingestion_runs`:** `{runs_count:,}` records")

            # Ingestion history table
            runs_cursor = col_runs.find({}, {"_id": 0}).sort("start_time", -1).limit(10)
            df_runs = pd.DataFrame(list(runs_cursor))
            st.markdown("#### Recent Ingestion Runs")
            if not df_runs.empty:
                st.dataframe(df_runs, use_container_width=True)
            else:
                st.info("No previous ingestion runs recorded.")

        with tab_quality:
            st.markdown("#### 🧪 Meteorological Attribute Completeness")
            dq = analytics.get_data_quality_report()
            total_recs = dq.get("total_records", 0)

            if total_recs > 0:
                metrics_dict = dq.get("metrics", {})
                quality_rows = []
                for field, stats in metrics_dict.items():
                    quality_rows.append({
                        "Field": field,
                        "Valid Count": stats["valid_count"],
                        "Missing/Null": stats["missing_count"],
                        "Completeness (%)": stats["completeness_pct"],
                    })
                df_quality = pd.DataFrame(quality_rows)
                st.dataframe(df_quality, use_container_width=True)

                fig_qual = px.bar(
                    df_quality,
                    x="Field",
                    y="Completeness (%)",
                    color="Completeness (%)",
                    color_continuous_scale="Blues",
                    range_y=[0, 100],
                    title="Data Quality Completeness by Field",
                )
                fig_qual.update_layout(height=350, template="plotly_dark")
                st.plotly_chart(fig_qual, use_container_width=True)
            else:
                st.info("No records to evaluate.")

        with tab_api_fetch:
            st.markdown("#### 🌐 Fetch Historical Weather Data from Open-Meteo")
            st.caption("Requests hourly historical observations and bulk upserts into local MongoDB.")

            all_cities = list(config.CITY_REGISTRY.keys())
            fetch_cities = st.multiselect("Select Cities", all_cities, default=["Bengaluru", "Delhi"])
            c_sdate, c_edate = st.columns(2)
            with c_sdate:
                f_s = st.date_input("Start Date", value=date(2023, 1, 1))
            with c_edate:
                f_e = st.date_input("End Date", value=date(2023, 1, 31))

            if st.button("🚀 Run API Ingestion"):
                if not fetch_cities:
                    st.error("Select at least one city.")
                elif f_s > f_e:
                    st.error("Start date must be before end date.")
                else:
                    with st.spinner("Fetching data from Open-Meteo and upserting into MongoDB..."):
                        code = weather_fetcher.run_fetcher(
                            cities=fetch_cities,
                            start_date_str=f_s.strftime("%Y-%m-%d"),
                            end_date_str=f_e.strftime("%Y-%m-%d"),
                        )
                        if code == 0:
                            st.success("✅ Ingestion completed successfully! Caches refreshed.")
                            st.rerun()
                        else:
                            st.error("❌ Ingestion encountered errors. Check logs.")

        with tab_csv_import:
            st.markdown("#### 📁 Import Local CSV File")
            st.caption("Select or upload a historical weather CSV file (e.g. from Kaggle) to ingest into MongoDB.")

            csv_file = st.file_uploader("Upload CSV file", type=["csv"])
            csv_city = st.selectbox("Default City (if absent from CSV)", [""] + all_cities)
            csv_gran = st.selectbox("Granularity", ["hourly", "daily"])

            if csv_file is not None:
                # Save uploaded file temporarily to data/
                temp_path = os.path.join("data", csv_file.name)
                with open(temp_path, "wb") as f:
                    f.write(csv_file.getbuffer())

                if st.button("📥 Import Uploaded CSV"):
                    with st.spinner("Processing CSV chunks and upserting into MongoDB..."):
                        res = import_data.import_csv_file(
                            file_path=temp_path,
                            default_city=csv_city if csv_city else None,
                            granularity=csv_gran,
                            source_name="uploaded_csv",
                        )
                        st.success(
                            f"Import Finished: Read {res['total_read']}, Accepted {res['accepted']}, "
                            f"Inserted {res['inserted']}, Updated {res['updated']}"
                        )
                        st.rerun()
