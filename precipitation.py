import logging

from pyowm import OWM


def get_preciptation(api_key: str = None, zip_code: str = None):
    """
    Get precipitation data for a zip code
    """
    try:
        owm = OWM(api_key)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_zip_code(zip_code, "US")
        weather = observation.weather
        observation_timestamp = weather.reference_time(timeformat="date")
        rain = weather.rain
        try:
            rain_mms = rain["1h"]
        except KeyError:
            logging.info("No rain in the last hour")
            rain_mms = 0
        return {"zip_code": zip_code, "observation_timestamp": observation_timestamp, "precipitation": rain_mms}
    except Exception:
        logging.error("Error getting precipitation data, check API key or number of requests")
        return None
