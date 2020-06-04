"""Constants."""

BASE_URL = "https://api.climacell.co/v3/weather"

REALTIME = "realtime"
FORECAST_NOWCAST = "nowcast"
FORECAST_HOURLY = "forecast/hourly"
FORECAST_DAILY = "forecast/daily"
HISTORICAL_CLIMACELL = "historical/climacell"
HISTORICAL_STATION = "historical/station"

FORECAST_NOWCAST_MAX_AGE = {"minutes": 360}
FORECAST_HOURLY_MAX_AGE = {"hours": 96}
FORECAST_DAILY_MAX_AGE = {"days": 15}
HISTORICAL_CLIMACELL_MAX_AGE = {"hours": 6}
HISTORICAL_STATION_MAX_INTERVAL = {"hours": 24}
HISTORICAL_STATION_MAX_AGE = {"weeks": 4}

HEADERS = {"content-type": "application/json"}

FIELDS = {
    "temp": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "feels_like": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "dewpoint": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "humidity": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "wind_speed": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "wind_direction": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "wind_gust": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "baro_pressure": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "precipitation": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "precipitation_type": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "precipitation_probability": [FORECAST_HOURLY, FORECAST_DAILY],
    "precipitation_accumulation": [FORECAST_DAILY],
    "sunrise": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
    ],
    "sunset": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
    ],
    "visibility": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "cloud_cover": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "cloud_base": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "cloud_ceiling": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
        HISTORICAL_STATION,
    ],
    "surface_shortwave_radiation": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
    ],
    "moon_phase": [REALTIME, FORECAST_HOURLY],
    "weather_code": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        FORECAST_DAILY,
        HISTORICAL_CLIMACELL,
    ],
    "weather_groups": [HISTORICAL_STATION],
    "pm25": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "pm10": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "o3": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "no2": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "co": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "so2": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "epa_aqi": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "epa_primary_pollutant": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
    ],
    "epa_health_concern": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
    ],
    "china_aqi": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "china_primary_pollutant": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
    ],
    "china_health_concern": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
    ],
    "pollen_tree": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "pollen_weed": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "pollen_grass": [REALTIME, FORECAST_NOWCAST, FORECAST_HOURLY, HISTORICAL_CLIMACELL],
    "road_risk_score": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
    ],
    "road_risk_confidence": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
    ],
    "road_risk_conditions": [
        REALTIME,
        FORECAST_NOWCAST,
        FORECAST_HOURLY,
        HISTORICAL_CLIMACELL,
    ],
    "fire_index": [REALTIME, HISTORICAL_CLIMACELL],
}
