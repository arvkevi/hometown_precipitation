import datetime
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
import streamlit as st

CONNECTION_URI = os.environ.get("CONNECTION_URI")
ZIP_CODE = os.environ.get("ZIP_CODE")

st.set_page_config(page_title="Last time it rained?", page_icon="rain", layout="wide")


@st.cache()
def get_latest_precipitation_data(
    connection_uri: str,
    zip_code: str,
    from_date: str,
):
    """
    Query the last rain event for a zip code
    """
    try:
        conn = psycopg2.connect(connection_uri)
    except psycopg2.OperationalError as conn_error:
        st.error("Unable to connect!\n{0}").format(conn_error)

    cur = conn.cursor()
    cur.execute(
        """
        SELECT zip_code, observation_timestamp, precipitation_mms FROM precipitation
        WHERE observation_timestamp <=
        ( SELECT MAX(observation_timestamp)
        FROM precipitation
        WHERE zip_code = %s
        AND observation_timestamp <= %s
        AND precipitation_mms > 0
        )
        AND observation_timestamp >=
        ( SELECT MAX(observation_timestamp)
        FROM precipitation
        WHERE zip_code = %s
        AND observation_timestamp <= %s
        AND precipitation_mms > 0
        ) - INTERVAL '3 DAYS'
        """,
        (zip_code, from_date, zip_code, from_date),
    )
    last_rain_data = cur.fetchall()
    column_names = ["zip_code", "observation_timestamp", "precipitation_mms"]
    return pd.DataFrame(last_rain_data, columns=column_names)


def get_last_30_days(
    connection_uri: str,
    zip_code: str,
):
    """
    Query the last 30 days of precipitation for a zip code
    """
    try:
        conn = psycopg2.connect(connection_uri)
    except psycopg2.OperationalError as conn_error:
        st.error("Unable to connect!\n{0}").format(conn_error)

    cur = conn.cursor()
    cur.execute(
        """
        SELECT zip_code, observation_timestamp, precipitation_mms FROM precipitation
        WHERE observation_timestamp >= NOW() - INTERVAL '30 DAYS'
        """,
        (zip_code, zip_code),
    )
    last_rain_data = cur.fetchall()
    column_names = ["zip_code", "observation_timestamp", "precipitation_mms"]
    return pd.DataFrame(last_rain_data, columns=column_names)


st.title(f"When did it last rain in zip code {ZIP_CODE}?")
from_date = st.date_input("From which date? Choose:", value=datetime.datetime.now())
data = get_latest_precipitation_data(CONNECTION_URI, ZIP_CODE, from_date)
last_thirty_days = get_last_30_days(CONNECTION_URI, ZIP_CODE)

last_rain_date = data["observation_timestamp"].max()
last_rain_mms = data.loc[
    data["observation_timestamp"] == data["observation_timestamp"].max(), "precipitation_mms"
].item()

col1, col2 = st.columns(2)
col1.metric("Last Rain Date", last_rain_date.strftime("%Y-%m-%d @ %H:%M"))
col2.metric("Last Rain (millimeters)", last_rain_mms)

last_thirty_days["24h_sum"] = last_thirty_days["precipitation_mms"].rolling(24, min_periods=1).sum()
# last 30 days of rain
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_title(f"Last 30 days of rain in zip code {ZIP_CODE}")
ax.plot(
    last_thirty_days["observation_timestamp"], last_thirty_days["precipitation_mms"], label="Precipitation in last hour"
)
ax.plot(last_thirty_days["observation_timestamp"], last_thirty_days["24h_sum"], label="24h sum (mm)")
locator = mdates.AutoDateLocator(minticks=3, maxticks=30)
formatter = mdates.ConciseDateFormatter(locator)
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(formatter)
ax.legend()
ax.set_ylabel("Precipitation (mm)")
# Hide the right and tp spines
ax.spines.right.set_visible(False)
ax.spines.top.set_visible(False)


st.pyplot(fig)
