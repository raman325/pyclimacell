"""Main module."""
from datetime import datetime, timedelta
import json
import logging
import pytz
from typing import Any, Dict, List, Optional, Union

from aiohttp import ClientConnectionError, ClientResponseError, ClientSession

from .const import (
    BASE_URL_V3,
    BASE_URL_V4,
    CURRENT,
    DAILY,
    FIELDS_V3,
    FIELDS_V4,
    FORECASTS,
    FORECAST_DAILY,
    FORECAST_DAILY_MAX_AGE,
    FORECAST_HOURLY,
    FORECAST_HOURLY_MAX_AGE,
    FORECAST_NOWCAST,
    FORECAST_NOWCAST_MAX_AGE,
    HEADERS,
    HISTORICAL_CLIMACELL,
    HISTORICAL_CLIMACELL_MAX_AGE,
    HISTORICAL_STATION,
    HISTORICAL_STATION_MAX_AGE,
    HISTORICAL_STATION_MAX_INTERVAL,
    HOURLY,
    NOWCAST,
    REALTIME,
)
from .exceptions import (
    CantConnectException,
    InvalidAPIKeyException,
    InvalidTimestep,
    MalformedRequestException,
    RateLimitedException,
    UnknownException,
)
from .helpers import async_to_sync

_LOGGER = logging.getLogger(__name__)


def process_v4_fields(fields: List[str], timestep: str) -> str:
    """
    Filter v4 field list to only include valid fields for a given endpoint.

    Logs a warning when fields get filtered out.
    """
    valid_fields = [field for field in fields if field in FIELDS_V4]
    if len(valid_fields) < len(fields):
        _LOGGER.warning(
            "Removed invalid fields: %s", list(set(fields) - set(valid_fields))
        )

    if timestep == timedelta(days=1):
        processed_fields = [
            field for field in valid_fields if FIELDS_V4[field]["timestep"][1] == 360
        ]
    elif timestep == timedelta(hours=1):
        processed_fields = [
            field for field in valid_fields if FIELDS_V4[field]["timestep"][1] >= 108
        ]
    elif timestep in (
        timedelta(minutes=30),
        timedelta(minutes=15),
        timedelta(minutes=5),
        timedelta(minutes=1),
    ):
        processed_fields = [
            field for field in valid_fields if FIELDS_V4[field]["timestep"][1] >= 6
        ]
    elif timestep == timedelta(0):
        processed_fields = [
            field
            for field in valid_fields
            if FIELDS_V4[field]["timestep"][0] <= 0
            and FIELDS_V4[field]["timestep"][1] >= 0
        ]
    elif timestep < timedelta(0):
        processed_fields = [
            field for field in valid_fields if FIELDS_V4[field]["timestep"][0] < 0
        ]
    else:
        raise InvalidTimestep

    if len(processed_fields) < len(valid_fields):
        _LOGGER.warning(
            "Remove fields not available for `%s` timestep: %s",
            timestep,
            list(set(valid_fields) - set(processed_fields)),
        )
    return processed_fields


def dt_to_utc(input_dt: datetime) -> datetime:
    """If input datetime has a timezone defined, convert to UTC."""
    if input_dt and input_dt.tzinfo:
        return input_dt.astimezone(pytz.utc)
    return input_dt


class ClimaCellV4:
    """Async class to query the ClimaCell v4 API."""

    def __init__(
        self,
        apikey: str,
        latitude: Union[int, float, str],
        longitude: Union[int, float, str],
        unit_system: str = "imperial",
        session: ClientSession = None,
    ) -> None:
        """Initialize ClimaCell API object."""
        if unit_system.lower() not in ("metric", "imperial", "si", "us"):
            raise ValueError("`unit_system` must be `metric` or `imperial`")
        elif unit_system.lower() == "si":
            unit_system = "metric"
        elif unit_system.lower() == "us":
            unit_system = "imperial"

        self._apikey = apikey
        self.location = [float(latitude), float(longitude)]
        self.unit_system = unit_system.lower()
        self._session = session
        self._params = {
            "location": self.location,
            "units": self.unit_system,
        }
        self._headers = {**HEADERS, "apikey": self._apikey}

    @staticmethod
    def convert_fields_to_measurements(fields: List[str]) -> List[str]:
        """Converts general field list into fields with measurements."""
        field_list = []
        for field in fields:
            measurements = FIELDS_V4[field]["measurements"]
            if len(measurements) < 2:
                field_list.append(field)
            else:
                field_list.extend(
                    [f"{field}{measurement}" for measurement in measurements]
                )

        return field_list

    @staticmethod
    def available_fields(
        timestep: timedelta, types: Optional[List] = None
    ) -> List[str]:
        "Return available fields for a given timestep."
        if timestep == timedelta(days=1):
            fields = [
                field for field in FIELDS_V4 if FIELDS_V4[field]["timestep"][1] == 360
            ]
        elif timestep == timedelta(hours=1):
            fields = [
                field for field in FIELDS_V4 if FIELDS_V4[field]["timestep"][1] >= 108
            ]
        elif timestep in (
            timedelta(minutes=30),
            timedelta(minutes=15),
            timedelta(minutes=5),
            timedelta(minutes=1),
        ):
            fields = [
                field for field in FIELDS_V4 if FIELDS_V4[field]["timestep"][1] >= 6
            ]
        elif timestep in (timedelta(0), CURRENT):
            fields = [
                field
                for field in FIELDS_V4
                if FIELDS_V4[field][0] <= 0 and FIELDS_V4[field]["timestep"][1] >= 0
            ]
        elif timestep < timedelta(0):
            fields = [
                field for field in FIELDS_V4 if FIELDS_V4[field]["timestep"][0] < 0
            ]
        else:
            raise InvalidTimestep

        if types:
            return [field for field in fields if FIELDS_V4[field]["type"] in types]

        return fields

    async def _call_api(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call ClimaCell API."""
        try:
            if self._session:
                resp = await self._session.post(
                    BASE_URL_V4,
                    headers=self._headers,
                    data=json.dumps({**self._params, **params}),
                )
                resp_json = await resp.json()
                if resp.status == 200:
                    return resp_json
                if resp.status == 400:
                    raise MalformedRequestException(resp_json)
                elif resp.status in (401, 403):
                    raise InvalidAPIKeyException(resp_json)
                elif resp.status == 429:
                    raise RateLimitedException(resp_json)
                else:
                    raise UnknownException(resp_json)

            async with ClientSession() as session:
                resp = await session.post(
                    BASE_URL_V4,
                    headers=self._headers,
                    data=json.dumps({**self._params, **params}),
                )
                resp_json = await resp.json()
                if resp.status == 200:
                    return resp_json
                if resp.status == 400:
                    raise MalformedRequestException(resp_json)
                elif resp.status in (401, 403):
                    raise InvalidAPIKeyException(resp_json)
                elif resp.status == 429:
                    raise RateLimitedException(resp_json)
                else:
                    raise UnknownException(resp_json)
        except ClientConnectionError:
            raise CantConnectException()

    async def realtime(self, fields: List[str]) -> Dict[str, Any]:
        """Return realtime weather conditions from ClimaCell API."""
        return await self._call_api(
            {
                "fields": process_v4_fields(fields, timedelta(0)),
                "timesteps": ["current"],
            }
        )

    async def _forecast(
        self,
        timestep: timedelta,
        fields: List[str],
        start_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return forecast data from ClimaCell's API for a given time period."""
        params = {
            "fields": self.convert_fields_to_measurements(
                process_v4_fields(fields, timestep)
            ),
            **kwargs,
        }
        if timestep == timedelta(days=1):
            params["timestep"] = ["1d"]
        elif timestep == timedelta(hours=1):
            params["timestep"] = ["1h"]
        elif timestep in (
            timedelta(minutes=30),
            timedelta(minutes=15),
            timedelta(minutes=5),
            timedelta(minutes=1),
        ):
            params["timestep"] = [f"{int(timestep.total_seconds()/60)}m"]
        else:
            raise InvalidTimestep

        if start_time:
            if not start_time.tzinfo:
                start_time.replace(tzinfo=pytz.utc)
            params["startTime"] = f"{start_time.replace(microsecond=0).isoformat()}"
        else:
            start_time = datetime.utcnow().replace(tzinfo=pytz.utc)
        if duration:
            end_time = (start_time + duration).replace(microsecond=0)
            params["endTime"] = f"{end_time.isoformat()}"

        return await self._call_api(params)

    async def forecast_nowcast(
        self,
        fields: List[str],
        start_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
        timestep: int = 5,
    ) -> Dict[str, Any]:
        """Return forecast data from ClimaCell's NowCast API for a given time period."""
        if timestep not in (1, 5, 15, 30):
            raise InvalidTimestep
        return await self._forecast(
            timedelta(minutes=timestep),
            fields,
            start_time=start_time,
            duration=duration,
        )

    async def forecast_daily(
        self,
        fields: List[str],
        start_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
    ) -> Dict[str, Any]:
        """Return daily forecast data from ClimaCell's API for a given time period."""
        return await self._forecast(
            timedelta(days=1), fields, start_time=start_time, duration=duration
        )

    async def forecast_hourly(
        self,
        fields: List[str],
        start_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
    ) -> Dict[str, Any]:
        """Return hourly forecast data from ClimaCell's API for a given time period."""
        return await self._forecast(
            timedelta(hours=1), fields, start_time=start_time, duration=duration
        )

    async def realtime_and_all_forecasts(
        self,
        realtime_fields: List[str],
        forecast_fields: List[str],
        nowcast_timestep: int = 5,
    ) -> Dict[str, Any]:
        """Return realtime weather and all forecasts."""
        ret_data = {}
        data = await self._call_api(
            {
                "timesteps": ["current"],
                "fields": realtime_fields,
            }
        )
        if (
            "data" in data
            and "timelines" in data["data"]
            and "intervals" in data["data"]["timelines"][0]
            and "values" in data["data"]["timelines"][0]["intervals"][0]
        ):
            ret_data[CURRENT] = data["data"]["timelines"][0]["intervals"][0]["values"]

        data = await self._call_api(
            {
                "timesteps": [f"{nowcast_timestep}m", "1h", "1d"],
                "fields": forecast_fields,
                "startTime": datetime.utcnow().replace(tzinfo=pytz.utc).isoformat(),
            }
        )
        if "data" in data and "timelines" in data["data"]:
            ret_data[FORECASTS] = {}
            for timeline in data["data"]["timelines"]:
                if timeline["timestep"] == "1d":
                    key = DAILY
                elif timeline["timestep"] == "1h":
                    key = HOURLY
                else:
                    key = NOWCAST
                ret_data[FORECASTS][key] = timeline["intervals"]

        return ret_data


class ClimaCellV4Sync(ClimaCellV4):
    """Synchronous class to query the ClimaCell API."""

    def __init__(
        self,
        apikey: str,
        latitude: Union[int, float, str],
        longitude: Union[int, float, str],
        unit_system: str = "imperial",
    ) -> None:
        """Initialize Synchronous ClimaCell v4 API object."""
        super().__init__(apikey, latitude, longitude, unit_system)

    @async_to_sync
    async def realtime(self, fields: List[str]) -> Dict[str, Any]:
        """Return realtime weather conditions from ClimaCell API."""
        return await super().realtime(fields)

    @async_to_sync
    async def forecast_nowcast(
        self,
        fields: List[str],
        start_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return forecast data from ClimaCell's NowCast API for a given time period."""
        return await super().forecast_nowcast(fields, start_time, duration, timestep)

    @async_to_sync
    async def forecast_daily(
        self,
        fields: List[str],
        start_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
    ) -> List[Dict[str, Any]]:
        """Return daily forecast data from ClimaCell's API for a given time period."""
        return await super().forecast_daily(fields, start_time, duration)

    @async_to_sync
    async def forecast_hourly(
        self,
        fields: List[str],
        start_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
    ) -> List[Dict[str, Any]]:
        """Return hourly forecast data from ClimaCell's API for a given time period."""
        return await super().forecast_hourly(fields, start_time, duration)

    @async_to_sync
    async def realtime_and_all_forecasts(
        self,
        realtime_fields: List[str],
        forecast_fields: List[str],
        nowcast_timestep: int = 5,
    ) -> Dict[str, Any]:
        """Return realtime weather and all forecasts."""
        return await super().realtime_and_all_forecasts(
            realtime_fields, forecast_fields, nowcast_timestep=nowcast_timestep
        )


def process_v3_fields(fields: List[str], endpoint: str) -> str:
    """
    Filter v3 field list to only include valid fields for a given endpoint.

    Logs a warning when fields get filtered out.
    """

    valid_fields = [field for field in fields if field in FIELDS_V3]
    if len(valid_fields) < len(fields):
        _LOGGER.warning(
            "Removed invalid fields: %s", list(set(fields) - set(valid_fields))
        )
    processed_fields = [field for field in valid_fields if endpoint in FIELDS_V3[field]]
    if len(processed_fields) < len(valid_fields):
        _LOGGER.warning(
            "Remove fields not available for `%s` endpoint: %s",
            endpoint,
            list(set(valid_fields) - set(processed_fields)),
        )
    return ",".join(processed_fields)


def validate_timerange(
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    duration: timedelta,
    max_age: Dict[str, float],
    max_interval: Optional[Dict[str, float]] = None,
) -> None:
    """
    Validate start and end time.

    Validates that no time exceeds max age and the difference between start and
    end doesn't exceed max interval.
    """
    now = datetime.utcnow()
    age_delta = timedelta(**max_age)
    interval_delta = timedelta(**max_interval) if max_interval else None

    if interval_delta and duration > interval_delta:
        raise ValueError(
            (
                "The duration specified exceeds the maximum interval of "
                f"{interval_delta}"
            )
        )

    if start_time:
        if start_time < now:
            raise ValueError("`start_time` must be now or in the future")
        if start_time - now + duration > age_delta:
            raise ValueError(
                (
                    "The `start_time` + `duration` exceeds the maximum forecastability "
                    f"of {age_delta} from now"
                )
            )

    if end_time:
        if end_time > now:
            raise ValueError("`end_time` must be now or in the past")

        if now - end_time - duration < age_delta:
            raise ValueError(
                (
                    "The `end_time` - `duration` exceeds the maximum historical data "
                    f"accessibility of {age_delta} from now"
                )
            )

    if duration > age_delta:
        raise ValueError(
            (
                "The duration specified exceeds the maximum forecastability or "
                f"historical data accessibility of {age_delta} from now"
            )
        )


class ClimaCellV3:
    """Async class to query the ClimaCell v3 API."""

    def __init__(
        self,
        apikey: str,
        latitude: Union[int, float, str],
        longitude: Union[int, float, str],
        unit_system: str = "us",
        session: ClientSession = None,
    ) -> None:
        """Initialize ClimaCell API object."""
        if unit_system.lower() not in ("us", "si"):
            raise ValueError("`unit_system` must be `si` or `us`")

        self._apikey = apikey
        self.latitude = str(latitude)
        self.longitude = str(longitude)
        self.unit_system = unit_system.lower()
        self._session = session
        self._params = {
            "lat": self.latitude,
            "lon": self.longitude,
            "unit_system": self.unit_system,
        }
        self._headers = {**HEADERS, "apikey": self._apikey}

    async def _call_api(
        self, relative_endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call ClimaCell API."""
        try:
            if self._session:
                resp = await self._session.get(
                    f"{BASE_URL_V3}/{relative_endpoint}",
                    headers=self._headers,
                    params={**self._params, **params},
                    raise_for_status=True,
                )
                return await resp.json()

            async with ClientSession() as session:
                resp = await session.get(
                    f"{BASE_URL_V3}/{relative_endpoint}",
                    headers=self._headers,
                    params={**self._params, **params},
                    raise_for_status=True,
                )
                return await resp.json()
        except ClientResponseError as error:
            if error.status == 400:
                raise MalformedRequestException()
            elif error.status in (401, 403):
                raise InvalidAPIKeyException()
            elif error.status == 429:
                raise RateLimitedException()
            else:
                raise UnknownException()
        except ClientConnectionError:
            raise CantConnectException()

    @staticmethod
    def available_fields(endpoint: str) -> List[str]:
        "Return available fields for a given endpoint."
        return [field for field in FIELDS_V3 if endpoint in FIELDS_V3[field]]

    @staticmethod
    def first_field(cls, endpoint: str) -> List[str]:
        "Return available fields for a given endpoint."
        return [cls.available_fields(endpoint)[0]]

    async def realtime(self, fields: List[str]) -> Dict[str, Any]:
        """Return realtime weather conditions from ClimaCell API."""
        return await self._call_api(
            REALTIME, {"fields": process_v3_fields(fields, REALTIME)}
        )

    async def _forecast(
        self,
        endpoint: str,
        max_age: Dict[str, float],
        fields: List[str],
        start_time: Optional[datetime],
        duration: timedelta,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return forecast data from ClimaCell's API for a given time period."""
        start_time = dt_to_utc(start_time)
        validate_timerange(start_time, None, duration, max_age)
        if start_time:
            params = {
                "fields": process_v3_fields(fields, endpoint),
                "start_time": f"{start_time.replace(microsecond=0).isoformat()}",
                "end_time": f"{(start_time + duration).replace(microsecond=0).isoformat()}",
                **kwargs,
            }
        else:
            params = {
                "fields": process_v3_fields(fields, endpoint),
                "end_time": f"{(datetime.utcnow() + duration).replace(microsecond=0).isoformat()}",
                **kwargs,
            }
        return await self._call_api(endpoint, params)

    async def forecast_nowcast(
        self,
        fields: List[str],
        start_time: Optional[datetime],
        duration: timedelta,
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return forecast data from ClimaCell's NowCast API for a given time period."""
        return await self._forecast(
            FORECAST_NOWCAST,
            FORECAST_NOWCAST_MAX_AGE,
            fields,
            start_time,
            duration,
            timestep=timestep,
        )

    async def forecast_daily(
        self, fields: List[str], start_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return daily forecast data from ClimaCell's API for a given time period."""
        return await self._forecast(
            FORECAST_DAILY, FORECAST_DAILY_MAX_AGE, fields, start_time, duration
        )

    async def forecast_hourly(
        self, fields: List[str], start_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return hourly forecast data from ClimaCell's API for a given time period."""
        return await self._forecast(
            FORECAST_HOURLY, FORECAST_HOURLY_MAX_AGE, fields, start_time, duration
        )

    async def _historical(
        self,
        endpoint: str,
        max_age: Dict[str, float],
        max_interval: Optional[Dict[str, float]],
        fields: List[str],
        end_time: Optional[datetime],
        duration: timedelta,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return historical data from ClimaCell's API for a given time period."""
        end_time = dt_to_utc(end_time)
        validate_timerange(None, end_time, duration, max_age, max_interval)
        if end_time:
            params = {
                "fields": process_v3_fields(fields, endpoint),
                "start_time": f"{(end_time - duration).replace(microsecond=0).isoformat()}",
                **kwargs,
            }
        else:
            params = {
                "fields": process_v3_fields(fields, endpoint),
                "start_time": f"{(datetime.utcnow() - duration).replace(microsecond=0).isoformat()}",
                "end_time": "now",
                **kwargs,
            }
        if end_time:
            params.update(
                {"end_time": f"{end_time.replace(microsecond=0).isoformat()}"}
            )
        else:
            params.update({"end_time": "now"})
        return await self._call_api(endpoint, params)

    async def historical_climacell(
        self,
        fields: List[str],
        end_time: Optional[datetime],
        duration: timedelta,
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return historical data from ClimaCell data."""
        return await self._historical(
            HISTORICAL_CLIMACELL,
            HISTORICAL_CLIMACELL_MAX_AGE,
            None,
            fields,
            end_time,
            duration,
            timestep=timestep,
        )

    async def historical_station(
        self, fields: List[str], end_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return historical data from weather stations."""
        return await self._historical(
            HISTORICAL_STATION,
            HISTORICAL_STATION_MAX_AGE,
            HISTORICAL_STATION_MAX_INTERVAL,
            fields,
            end_time,
            duration,
        )


class ClimaCellV3Sync(ClimaCellV3):
    """Synchronous class to query the ClimaCell API."""

    def __init__(
        self,
        apikey: str,
        latitude: Union[int, float, str],
        longitude: Union[int, float, str],
        unit_system: str = "us",
    ) -> None:
        """Initialize Synchronous ClimaCell v3 API object."""
        super().__init__(apikey, latitude, longitude, unit_system)

    @async_to_sync
    async def realtime(self, fields: List[str]) -> Dict[str, Any]:
        """Return realtime weather conditions from ClimaCell API."""
        return await super().realtime(fields)

    @async_to_sync
    async def forecast_nowcast(
        self,
        fields: List[str],
        start_time: Optional[datetime],
        duration: timedelta,
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return forecast data from ClimaCell's NowCast API for a given time period."""
        return await super().forecast_nowcast(fields, start_time, duration, timestep)

    @async_to_sync
    async def forecast_daily(
        self, fields: List[str], start_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return daily forecast data from ClimaCell's API for a given time period."""
        return await super().forecast_daily(fields, start_time, duration)

    @async_to_sync
    async def forecast_hourly(
        self, fields: List[str], start_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return hourly forecast data from ClimaCell's API for a given time period."""
        return await super().forecast_hourly(fields, start_time, duration)

    @async_to_sync
    async def historical_climacell(
        self,
        fields: List[str],
        end_time: Optional[datetime],
        duration: timedelta,
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return historical data from ClimaCell data."""
        return await super().historical_climacell(fields, end_time, duration, timestep)

    @async_to_sync
    async def historical_station(
        self, fields: List[str], end_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return historical data from weather stations."""
        return await super().historical_station(fields, end_time, duration)
