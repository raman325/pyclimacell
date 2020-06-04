"""Main module."""
from aiohttp import ClientSession
import logging
from typing import List, Dict, Any, Optional
from pyclimacell.const import (
    BASE_URL,
    HEADERS,
    REALTIME,
    FIELDS,
    FORECAST_DAILY,
    FORECAST_DAILY_MAX_AGE,
    FORECAST_HOURLY,
    FORECAST_HOURLY_MAX_AGE,
    FORECAST_NOWCAST,
    FORECAST_NOWCAST_MAX_AGE,
    HISTORICAL_CLIMACELL,
    HISTORICAL_STATION,
    HISTORICAL_CLIMACELL_MAX_AGE,
    HISTORICAL_STATION_MAX_AGE,
    HISTORICAL_STATION_MAX_INTERVAL,
)
from datetime import datetime, timedelta

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
    max_age: Dict[str, float],
    max_interval: Optional[Dict[str, float]],
) -> None:
    """
    Validate start and end time.

    Validates that no time exceeds max age and the difference between start and
    end doesn't exceed max interval.
    """
    if not start_time:
        start_time = datetime.utcnow()
    if not end_time:
        end_time = datetime.utcnow()
    if end_time < start_time:
        raise ValueError("`end_time` must be greater than `start_time`")
    age_delta = timedelta(**max_age)
    if end_time > datetime.utcnow() + age_delta:
        raise ValueError(
            f"`end_time` exceeds the maximum age of {age_delta} (HH:MM:SS) from now"
        )
    if start_time > datetime.utcnow() + age_delta:
        raise ValueError(
            f"`start_time` exceeds the maximum age of {age_delta} (HH:MM:SS) from now"
        )
    if max_interval:
        interval_delta = timedelta(**max_interval)
        if end_time - start_time > interval_delta:
            raise ValueError(
                (
                    "The time intervel between `start_time` and `end_time` exceeds the"
                    f"maximum interval of {interval_delta} (HH:MM:SS)"
                )
            )


class ClimaCellAPI:
    """Async class to query the ClimaCell API."""

    def __init__(
        self,
        apikey: str,
        latitude: str,
        longitude: str,
        unit_system: str = "us",
        session: ClientSession = None,
    ):
        """Initialize ClimaCell API object."""
        if unit_system.lower() not in ("us", "si"):
            raise ValueError("`unit_system` must be `si` or `us`")

        self.apikey = apikey
        self.latitude = latitude
        self.longitude = longitude
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
        end_time: datetime,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return forecast data from ClimaCell's API for a given time period."""
        validate_timerange(start_time, end_time, max_age)
        params = {
            "fields": process_fields(fields, endpoint),
            "end_time": f"{end_time.replace(microsecond=0).isoformat()}",
            **kwargs,
        }
        if start_time:
            params.update(
                {"start_time": f"{start_time.replace(microsecond=0).isoformat()}"}
            )
        return await self._call_api(endpoint, params)

    async def forecast_nowcast(
        self,
        fields: List[str],
        start_time: Optional[datetime],
        end_time: datetime,
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return forecast data from ClimaCell's NowCast API for a given time period."""
        return await self._forecast(
            FORECAST_NOWCAST,
            FORECAST_NOWCAST_MAX_AGE,
            fields,
            start_time,
            end_time,
            timestep=timestep,
        )

    async def forecast_daily(
        self, fields: List[str], start_time: Optional[datetime], end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Return daily forecast data from ClimaCell's API for a given time period."""
        return await self._forecast(
            FORECAST_DAILY, FORECAST_DAILY_MAX_AGE, fields, start_time, end_time
        )

    async def forecast_hourly(
        self, fields: List[str], start_time: Optional[datetime], end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Return hourly forecast data from ClimaCell's API for a given time period."""
        return await self._forecast(
            FORECAST_HOURLY, FORECAST_HOURLY_MAX_AGE, fields, start_time, end_time
        )

    async def _historical(
        self,
        endpoint: str,
        max_age: Dict[str, float],
        max_interval: Optional[Dict[str, float]],
        fields: List[str],
        start_time: datetime,
        end_time: Optional[datetime],
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Return historical data from ClimaCell's API for a given time period."""
        validate_timerange(start_time, end_time, max_age, max_interval)
        params = {
            "fields": process_fields(fields, endpoint),
            "start_time": f"{start_time.replace(microsecond=0).isoformat()}",
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
        start_time: datetime,
        end_time: Optional[datetime],
        timestep: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrurn historical data from ClimaCell data."""
        return await self._historical(
            HISTORICAL_CLIMACELL,
            HISTORICAL_CLIMACELL_MAX_AGE,
            None,
            fields,
            start_time,
            end_time,
            timestep=timestep,
        )

    async def historical_station(
        self, fields: List[str], start_time: datetime, end_time: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Retrurn historical data from weather stations."""
        return await self._historical(
            HISTORICAL_STATION,
            HISTORICAL_STATION_MAX_AGE,
            HISTORICAL_STATION_MAX_INTERVAL,
            fields,
            start_time,
            end_time,
        )
