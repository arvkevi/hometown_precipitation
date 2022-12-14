import datetime
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
import streamlit as st

from pyzipcode import ZipCodeDatabase

CONNECTION_URI = os.environ.get("CONNECTION_URI")
ZIP_CODE = os.environ.get("ZIP_CODE")

utc_offset = ZipCodeDatabase()[int(ZIP_CODE)].timezone

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
        WHERE observation_timestamp =
        ( SELECT MAX(observation_timestamp)
        FROM precipitation
        WHERE zip_code = %s
        AND observation_timestamp <= %s
        AND precipitation_mms > 0
        )
        """,
        (zip_code, from_date),
    )
    last_rain_data = cur.fetchall()
    conn.close()
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
        AND zip_code = %s
        """,
        (zip_code,),
    )
    last_rain_data = cur.fetchall()
    conn.close()
    column_names = ["zip_code", "observation_timestamp", "precipitation_mms"]
    return pd.DataFrame(last_rain_data, columns=column_names)


st.title(f"When did it last rain in zip code {ZIP_CODE}?")
from_date = st.date_input("From which date? Choose:", value=datetime.datetime.now())
# include the hours of the day on the from_date (for example, today...)
from_date = from_date + datetime.timedelta(hours=23, minutes=59, seconds=59)
data = get_latest_precipitation_data(CONNECTION_URI, ZIP_CODE, from_date)
# convert to local tz
data["observation_timestamp"] = data["observation_timestamp"].apply(
    lambda row: row + datetime.timedelta(hours=utc_offset)
)
last_thirty_days = get_last_30_days(CONNECTION_URI, ZIP_CODE)
# convert to local tz
last_thirty_days["observation_timestamp"] = last_thirty_days["observation_timestamp"].apply(
    lambda row: row + datetime.timedelta(hours=utc_offset)
)


last_rain_date = data["observation_timestamp"].max()
last_rain_mms = data.loc[
    data["observation_timestamp"] == data["observation_timestamp"].max(), "precipitation_mms"
].item()

col1, col2 = st.columns(2)
col1.metric("Last Rain Date (local time)", last_rain_date.strftime("%Y-%m-%d @ %H:%M"))
col2.metric("Last Rain (millimeters)", last_rain_mms)

last_thirty_days["24h_sum"] = last_thirty_days["precipitation_mms"].rolling(24, min_periods=1).sum()
# last 30 days of rain
fig, ax = plt.subplots(figsize=(8, 4))
ax.set_title(f"Last 30 days of rain in zip code {ZIP_CODE}")
ax.bar(
    last_thirty_days["observation_timestamp"],
    last_thirty_days["precipitation_mms"],
    width=0.25,
    label="Precipitation in last hour",
    color=["#fb8500"] * len(last_thirty_days),
)
ax.plot(last_thirty_days["observation_timestamp"], last_thirty_days["24h_sum"], label="24h sum (mm)", color="#023e8a")
ax.bar(
    last_thirty_days.loc[last_thirty_days["observation_timestamp"] == last_rain_date, "observation_timestamp"],
    last_thirty_days.loc[last_thirty_days["observation_timestamp"] == last_rain_date, "precipitation_mms"],
    width=0.25,
    label="Last rain event since'from_date'",
    color=["#fb8500"],
    hatch="//",
)
# ax.vlines(last_rain_date, 0, -0.5, linestyles="dashed", label="Last rain", color="red")
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
