"""Main module."""
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Union

from aiohttp import ClientConnectionError, ClientResponseError, ClientSession

from .const import (
    BASE_URL,
    FIELDS,
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
    REALTIME,
)
from .helpers import async_to_sync

_LOGGER = logging.getLogger(__name__)


def process_fields(fields: List[str], relative_endpoint: str) -> str:
    """
    Filter field list to only include valid fields for a given endpoint.

    Logs a warning when fields get filtered out.
    """
    valid_fields = [field for field in fields if field in FIELDS]
    if len(valid_fields) < len(fields):
        _LOGGER.warning(
            "Removed invalid fields: %s", list(set(fields) - set(valid_fields))
        )
    processed_fields = [
        field for field in valid_fields if relative_endpoint in FIELDS[field]
    ]
    if len(processed_fields) < len(valid_fields):
        _LOGGER.warning(
            "Remove fields not available for `%s` endpoint: %s",
            relative_endpoint,
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


class ClimaCell:
    """Async class to query the ClimaCell API."""

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

        self.apikey = apikey
        self.latitude = str(latitude)
        self.longitude = str(longitude)
        self.unit_system = unit_system.lower()
        self.session = session
        self.params = {
            "lat": self.latitude,
            "lon": self.longitude,
            "unit_system": self.unit_system,
            "apikey": self.apikey,
        }

    async def _call_api(
        self, relative_endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call ClimaCell API."""
        try:
            if self.session:
                resp = await self.session.get(
                    f"{BASE_URL}/{relative_endpoint}",
                    headers=HEADERS,
                    params={**params, **self.params},
                    raise_for_status=True,
                )
                return await resp.json()

            async with ClientSession() as session:
                resp = await session.get(
                    f"{BASE_URL}/{relative_endpoint}",
                    headers=HEADERS,
                    params={**params, **self.params},
                    raise_for_status=True,
                )
                return await resp.json()
        except ClientResponseError as error:
            if error.status == 400:
                raise MalformedRequestException(
                    error.request_info,
                    error.history,
                    status=error.status,
                    message=error.message,
                )
            elif error.status in (401, 403):
                raise InvalidAPIKeyException(
                    error.request_info,
                    error.history,
                    status=error.status,
                    message=error.message,
                )
            elif error.status == 429:
                raise RateLimitedException(
                    error.request_info,
                    error.history,
                    status=error.status,
                    message=error.message,
                )
            else:
                raise UnknownException(
                    error.request_info,
                    error.history,
                    status=error.status,
                    message=error.message,
                )
        except ClientConnectionError as error:
            raise CantConnectException(*error.args)

    @staticmethod
    def availabile_fields(endpoint: str) -> List[str]:
        "Return available fields for a given endpoint."
        return [field for field in FIELDS if endpoint in FIELDS[field]]

    @staticmethod
    def first_field(endpoint: str) -> List[str]:
        "Return available fields for a given endpoint."
        return [ClimaCell.availabile_fields(endpoint)[0]]

    async def realtime(self, fields: List[str]) -> Dict[str, Any]:
        """Return realtime weather conditions from ClimaCell API."""
        return await self._call_api(
            REALTIME, {"fields": process_fields(fields, REALTIME)}
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
        validate_timerange(start_time, None, duration, max_age)
        if start_time:
            params = {
                "fields": process_fields(fields, endpoint),
                "start_time": f"{start_time.replace(microsecond=0).isoformat()}",
                "end_time": f"{(start_time + duration).replace(microsecond=0).isoformat()}",
                **kwargs,
            }
        else:
            params = {
                "fields": process_fields(fields, endpoint),
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
        validate_timerange(None, end_time, duration, max_age, max_interval)
        if end_time:
            params = {
                "fields": process_fields(fields, endpoint),
                "start_time": f"{(end_time - duration).replace(microsecond=0).isoformat()}",
                **kwargs,
            }
        else:
            params = {
                "fields": process_fields(fields, endpoint),
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


class ClimaCellSync(ClimaCell):
    """Synchronous class to query the ClimaCell API."""

    def __init__(
        self,
        apikey: str,
        latitude: Union[int, float, str],
        longitude: Union[int, float, str],
        unit_system: str = "us",
    ) -> None:
        """Initialize Synchronous ClimaCell API object."""
        super(ClimaCellSync, self).__init__(apikey, latitude, longitude, unit_system)

    @async_to_sync
    async def realtime(self, fields: List[str]) -> Dict[str, Any]:
        """Return realtime weather conditions from ClimaCell API."""
        return await super(ClimaCellSync, self).realtime(fields)

    @async_to_sync
    async def forecast_nowcast(
        self,
        fields: List[str],
        start_time: Optional[datetime],
        duration: timedelta,
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return forecast data from ClimaCell's NowCast API for a given time period."""
        return await super(ClimaCellSync, self).forecast_nowcast(
            fields, start_time, duration, timestep
        )

    @async_to_sync
    async def forecast_daily(
        self, fields: List[str], start_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return daily forecast data from ClimaCell's API for a given time period."""
        return await super(ClimaCellSync, self).forecast_daily(
            fields, start_time, duration
        )

    @async_to_sync
    async def forecast_hourly(
        self, fields: List[str], start_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return hourly forecast data from ClimaCell's API for a given time period."""
        return await super(ClimaCellSync, self).forecast_hourly(
            fields, start_time, duration
        )

    @async_to_sync
    async def historical_climacell(
        self,
        fields: List[str],
        end_time: Optional[datetime],
        duration: timedelta,
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return historical data from ClimaCell data."""
        return await super(ClimaCellSync, self).historical_climacell(
            fields, end_time, duration, timestep
        )

    @async_to_sync
    async def historical_station(
        self, fields: List[str], end_time: Optional[datetime], duration: timedelta
    ) -> List[Dict[str, Any]]:
        """Return historical data from weather stations."""
        return await super(ClimaCellSync, self).historical_station(
            fields, end_time, duration
        )


class MalformedRequestException(ClientResponseError):
    """Raised when request was malformed."""


class InvalidAPIKeyException(ClientResponseError):
    """Raised when API key is invalid."""


class RateLimitedException(ClientResponseError):
    """Raised when API rate limit has been exceeded."""


class UnknownException(ClientResponseError):
    """Raised when unknown error occurs."""


class CantConnectException(ClientConnectionError):
    """Raise when client can't connect to ClimaCell API."""
